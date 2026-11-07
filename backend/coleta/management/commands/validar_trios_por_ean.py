"""Completa preços de três redes por consulta direta de código de barras.

Prioriza produtos que já têm preços em duas redes; depois tenta EANs
existentes em uma rede. Em último lugar testa uma pequena amostra de
produtos reais encontrados no Carrefour. NUNCA persiste um par isolado.
"""

from collections import defaultdict
from datetime import timedelta
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from catalogo.models import Produto, Supermercado
from coleta.atacadao import criar_sessao as sessao_atacadao
from coleta.carrefour import buscar_produtos as buscar_carrefour
from coleta.management.commands.triangular_precos import (
    LOJAS,
    normalizar_oferta,
    total_em_tres_redes,
)
from coleta.savegnago import criar_sessao as sessao_savegnago
from coleta.vtex_ean import buscar_ean
from precos.models import OfertaFonte, Preco


CEP = "14010000"
TERMOS_SEMENTE = ("detergente", "feijão", "arroz", "leite")
HORAS_PRECO_RECENTE = 36


class Command(BaseCommand):
    help = "Busca preços nas três redes por EAN exato, sem criar ofertas isoladas."

    def add_arguments(self, parser):
        parser.add_argument("--gravar", action="store_true")
        parser.add_argument("--cep", default=CEP)
        parser.add_argument("--max-eans", type=int, default=75)
        parser.add_argument("--max-buscas-carrefour", type=int, default=12)
        parser.add_argument("--sem-seeds", action="store_true")

    def handle(self, *args, **options):
        cep = "".join(c for c in str(options["cep"]) if c.isdigit())
        max_eans = options["max_eans"]
        max_carrefour = options["max_buscas_carrefour"]
        if len(cep) != 8:
            raise CommandError("CEP inválido.")
        if not 1 <= max_eans <= 120:
            raise CommandError("--max-eans deve estar entre 1 e 120.")
        if not 0 <= max_carrefour <= 25:
            raise CommandError("--max-buscas-carrefour deve estar entre 0 e 25.")

        agora = timezone.now()
        limite = agora - timedelta(hours=HORAS_PRECO_RECENTE)
        candidatos = defaultdict(dict)
        for oferta in (
            OfertaFonte.objects.filter(
                ativo=True,
                supermercado__ativo=True,
                produto__codigo_barras__isnull=False,
                supermercado__nome__in=LOJAS,
            )
            .select_related("supermercado", "produto")
        ):
            ean = str(oferta.produto.codigo_barras or "").strip()
            if not ean.isdigit() or len(ean) not in (8, 12, 13, 14):
                continue
            preco = oferta.precos.order_by("-data_hora_coleta", "-id").first()
            if not preco or preco.data_hora_coleta < limite:
                continue
            candidatos[ean][oferta.supermercado.nome] = {
                "ean": ean,
                "nome": oferta.produto.nome,
                "marca": oferta.produto.marca,
                "sku": oferta.codigo_externo,
                "valor": preco.valor,
                "url": oferta.url_fonte,
                "imagem": oferta.produto.imagem_url or "",
            }

        stats = {
            "trios_antes": total_em_tres_redes(),
            "candidatos_banco": len(candidatos),
            "consultas_ean": 0,
            "consultas_carrefour": 0,
            "encontrados_vtex": 0,
            "trios_verificados": 0,
            "trios_gravados": 0,
            "ofertas_criadas": 0,
            "precos_criados": 0,
            "falhas": 0,
        }

        sessoes = {}
        cache_ean = {}
        cache_carrefour = {}
        marcas_consultadas = set()
        trios_processados = set()
        trios_confirmados = set()

        def consultar_por_ean(loja, ean):
            chave = (loja, ean)
            if chave in cache_ean:
                return cache_ean[chave]
            stats["consultas_ean"] += 1
            try:
                if loja not in sessoes:
                    sessoes[loja] = (
                        sessao_savegnago(cep)
                        if loja == "Savegnago"
                        else sessao_atacadao(cep)
                    )
                bruto = buscar_ean(loja, ean, sessoes[loja])
                encontrado = normalizar_oferta(bruto, loja)
            except Exception as erro:
                stats["falhas"] += 1
                self.stderr.write(
                    f"[trio-ean] Falha consulta {loja} EAN {ean}: {erro}"
                )
                encontrado = None
            if encontrado and encontrado["ean"] == ean:
                stats["encontrados_vtex"] += 1
            else:
                encontrado = None
            cache_ean[chave] = encontrado
            return encontrado

        def consultar_carrefour_por_marca(termo):
            chave = str(termo or "").strip().casefold()
            if len(chave) < 3:
                return
            if chave in marcas_consultadas:
                return
            if stats["consultas_carrefour"] >= max_carrefour:
                return
            marcas_consultadas.add(chave)
            stats["consultas_carrefour"] += 1
            try:
                bruto = buscar_carrefour(termo=chave, quantidade=12)
            except Exception as erro:
                stats["falhas"] += 1
                self.stderr.write(
                    f"[trio-ean] Falha na busca Carrefour ({chave}): {erro}"
                )
                return
            for item in bruto:
                oferta = normalizar_oferta(item, "Carrefour")
                if oferta:
                    cache_carrefour[oferta["ean"]] = oferta

        def persistir_trio(ean, ofertas):
            if not options["gravar"]:
                return
            with transaction.atomic():
                produto = Produto.objects.filter(codigo_barras=ean).first()
                if produto is None:
                    origem = ofertas["Savegnago"]
                    produto = Produto.objects.create(
                        nome=origem["nome"],
                        marca=origem["marca"],
                        codigo_barras=ean,
                        imagem_url=origem["imagem"] or None,
                    )
                for loja, item in ofertas.items():
                    supermercado, _ = Supermercado.objects.get_or_create(
                        nome=loja,
                        defaults={
                            "endereco": "", "complemento": "",
                            "cidade": "Ribeirão Preto", "estado": "SP",
                            "site_url": LOJAS[loja], "ativo": True,
                        },
                    )
                    ativa = OfertaFonte.objects.filter(
                        produto=produto, supermercado=supermercado,
                        ativo=True,
                    ).first()
                    if ativa is None:
                        if OfertaFonte.objects.filter(
                            produto=produto, supermercado=supermercado
                        ).exists():
                            raise ValueError(
                                "Existe oferta inativa; não reativar."
                            )
                        ativa = OfertaFonte.objects.create(
                            produto=produto, supermercado=supermercado,
                            codigo_externo=item["sku"][:50],
                            nome_externo=item["nome"][:200],
                            url_fonte=item["url"], ativo=True,
                        )
                        stats["ofertas_criadas"] += 1
                    ultimo = ativa.precos.order_by(
                        "-data_hora_coleta", "-id"
                    ).first()
                    if ultimo is None or ultimo.valor != item["valor"]:
                        Preco.objects.create(
                            oferta_fonte=ativa, valor=item["valor"],
                            data_hora_coleta=timezone.now(),
                        )
                        stats["precos_criados"] += 1
            stats["trios_gravados"] += 1

        def processar(ean, ofertas):
            if ean in trios_confirmados:
                return
            if ean in trios_processados and "Carrefour" not in ofertas:
                return
            trios_processados.add(ean)

            for loja in ("Savegnago", "Atacadão"):
                if loja not in ofertas:
                    resultado = consultar_por_ean(loja, ean)
                    if resultado:
                        ofertas[loja] = resultado
            if not ("Savegnago" in ofertas and "Atacadão" in ofertas):
                return

            if "Carrefour" not in ofertas:
                if ean not in cache_carrefour:
                    origem = ofertas["Savegnago"]
                    termo = (
                        origem["marca"] or ofertas["Atacadão"]["marca"]
                        or origem["nome"].split()[0]
                    )
                    consultar_carrefour_por_marca(termo)
                if ean in cache_carrefour:
                    ofertas["Carrefour"] = cache_carrefour[ean]

            if all(loja in ofertas for loja in LOJAS):
                trios_confirmados.add(ean)
                stats["trios_verificados"] += 1
                self.stdout.write(
                    f"[trio-ean] CONFIRMADO {ean}: "
                    f"{ofertas['Savegnago']['nome']} | "
                    f"Savegnago R$ {ofertas['Savegnago']['valor']} | "
                    f"Atacadão R$ {ofertas['Atacadão']['valor']} | "
                    f"Carrefour R$ {ofertas['Carrefour']['valor']}"
                )
                try:
                    persistir_trio(ean, ofertas)
                except Exception as erro:
                    stats["falhas"] += 1
                    self.stderr.write(
                        f"[trio-ean] Não foi possível gravar {ean}: {erro}"
                    )

        self.stdout.write(
            f"[trio-ean] Avaliando até {max_eans} de {len(candidatos)} "
            "EANs já registrados, priorizando os que têm duas redes."
        )
        ordenados = sorted(
            candidatos.items(),
            key=lambda entrada: (
                -len(entrada[1]),
                "Carrefour" not in entrada[1],
                "Atacadão" not in entrada[1],
                entrada[0],
            ),
        )
        for indice, (ean, ofertas) in enumerate(ordenados[:max_eans], 1):
            processar(ean, ofertas)
            if indice % 10 == 0:
                self.stdout.write(
                    f"[trio-ean] {indice}/{min(max_eans, len(candidatos))} "
                    f"EANs testados; {stats['trios_verificados']} trios."
                )

        # Descobre EANs populares diretamente no Carrefour e procura o mesmo
        # código de barras nas duas lojas VTEX antes de salvar qualquer coisa.
        if not options["sem_seeds"] and stats["trios_verificados"] < 3:
            for termo in TERMOS_SEMENTE:
                if stats["consultas_carrefour"] >= max_carrefour:
                    break
                consultar_carrefour_por_marca(termo)
                pesquisados = 0
                for ean, item in list(cache_carrefour.items()):
                    if ean in trios_confirmados:
                        continue
                    contexto = dict(candidatos.get(ean, {}))
                    contexto["Carrefour"] = item
                    processar(ean, contexto)
                    pesquisados += 1
                    if pesquisados >= 6:
                        break

        stats["trios_depois"] = total_em_tres_redes()
        self.stdout.write(
            "[trio-ean] RESULTADO " +
            json.dumps(stats, ensure_ascii=False, sort_keys=True)
        )
        if not options["gravar"]:
            self.stdout.write("[trio-ean] SIMULAÇÃO: banco inalterado.")

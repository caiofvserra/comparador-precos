"""Amplia os itens comparáveis nas três redes, sem cadastrar produtos isolados.

Fase 1: busca paginada de *todos* os SKUs com preço no Savegnago e
Atacadão; fase 2: procura no Carrefour apenas os EANs da interseção.
Executar sob flag explícita no Render, nunca em toda requisição web.
"""

from collections import Counter, defaultdict
from datetime import timedelta
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalogo.models import Produto, Supermercado
from coleta.atacadao import criar_sessao as sessao_atacadao
from coleta.carrefour import buscar_produtos as buscar_carrefour
from coleta.management.commands.triangular_precos import (
    LOJAS, normalizar_oferta, total_em_tres_redes,
)
from coleta.savegnago import criar_sessao as sessao_savegnago
from coleta.vtex_paginado import buscar_paginado
from precos.models import OfertaFonte, Preco


TERMOS = {
    1: ("arroz", "feijão", "leite", "café", "macarrão", "detergente",
        "biscoito", "refrigerante", "doce", "sabão", "farinha", "molho"),
    2: ("açúcar", "oleo", "azeite", "sal", "maionese", "bolacha", "suco",
        "iogurte", "chocolate", "shampoo", "sabonete", "amaciante"),
    3: ("nestle", "italac", "piracanjuba", "camil", "quaker", "nissin",
        "marilan", "pilao", "coca", "ypê", "yoki", "panco"),
}

CARREFOUR_SEMENTES = {
    1: ("biscoito", "feijão", "leite", "detergente", "arroz",
        "macarrão", "café", "doce de leite", "refrigerante"),
    2: ("açúcar", "azeite", "óleo", "bolacha", "iogurte",
        "sabonete", "chocolate", "suco", "sabão"),
    3: ("nestle", "italac", "piracanjuba", "camil", "marilan",
        "nissin", "ypê", "yoki", "pilão"),
}
CEP = "14010000"


def ofertas_atuais_banco(horas=36):
    """Somente preços realmente coletados e com data recente."""
    limite = timezone.now() - timedelta(hours=horas)
    saida = defaultdict(dict)
    for oferta in (
        OfertaFonte.objects.filter(
            ativo=True, supermercado__ativo=True,
            supermercado__nome__in=LOJAS,
            produto__codigo_barras__isnull=False,
        ).select_related("supermercado", "produto")
    ):
        preco = oferta.precos.order_by("-data_hora_coleta", "-id").first()
        if preco is None or preco.data_hora_coleta < limite:
            continue
        ean = str(oferta.produto.codigo_barras or "").strip()
        if not ean.isdigit() or len(ean) not in (8, 12, 13, 14):
            continue
        saida[ean][oferta.supermercado.nome] = {
            "ean": ean, "nome": oferta.produto.nome,
            "marca": oferta.produto.marca, "valor": preco.valor,
            "url": oferta.url_fonte, "sku": oferta.codigo_externo,
            "imagem": oferta.produto.imagem_url or "",
        }
    return saida


def salvar_trio(ean, ofertas):
    """Transação atômica; grava histórico só quando preço mudou."""
    with transaction.atomic():
        produto = Produto.objects.filter(codigo_barras=ean).order_by("id").first()
        if produto is None:
            origem = ofertas["Savegnago"]
            produto = Produto.objects.create(
                nome=origem["nome"][:200],
                marca=origem["marca"][:100],
                codigo_barras=ean,
                imagem_url=origem["imagem"] or None,
            )

        novas = 0
        for loja in LOJAS:
            item = ofertas[loja]
            supermercado, _ = Supermercado.objects.get_or_create(
                nome=loja,
                defaults={
                    "endereco": "", "cidade": "Ribeirão Preto",
                    "estado": "SP", "site_url": LOJAS[loja], "ativo": True,
                },
            )
            oferta = OfertaFonte.objects.filter(
                produto=produto, supermercado=supermercado, ativo=True
            ).first()
            if oferta is None:
                if OfertaFonte.objects.filter(
                    produto=produto, supermercado=supermercado
                ).exists():
                    raise ValueError("Oferta inativa exige revisão manual.")
                oferta = OfertaFonte.objects.create(
                    produto=produto, supermercado=supermercado,
                    nome_externo=item["nome"][:200],
                    codigo_externo=item["sku"][:50],
                    url_fonte=item["url"], ativo=True,
                )
            anterior = oferta.precos.order_by(
                "-data_hora_coleta", "-id"
            ).first()
            if anterior is None or anterior.valor != item["valor"]:
                Preco.objects.create(
                    oferta_fonte=oferta, valor=item["valor"],
                    data_hora_coleta=timezone.now(),
                )
                novas += 1
    return novas


class Command(BaseCommand):
    help = "Varredura de SKUs de duas redes e confirmação de EAN no Carrefour."

    def add_arguments(self, parser):
        parser.add_argument("--gravar", action="store_true")
        parser.add_argument("--lote", type=int, default=1)
        parser.add_argument("--cep", default=CEP)
        parser.add_argument("--paginas", type=int, default=3)
        parser.add_argument("--tamanho", type=int, default=30)
        parser.add_argument("--buscas-carrefour", type=int, default=22)
        parser.add_argument("--itens-carrefour", type=int, default=16)

    def handle(self, *args, **options):
        lote = options["lote"]
        paginas = options["paginas"]
        tamanho = options["tamanho"]
        max_buscas = options["buscas_carrefour"]
        itens = options["itens_carrefour"]
        cep = "".join(x for x in str(options["cep"]) if x.isdigit())
        if lote not in TERMOS or len(cep) != 8:
            raise CommandError("Lote/CEP inválido.")
        if not 1 <= paginas <= 6 or not 1 <= tamanho <= 40:
            raise CommandError("Paginação fora do limite.")
        if not 1 <= max_buscas <= 40 or not 1 <= itens <= 30:
            raise CommandError("Limite Carrefour fora do permitido.")

        dados = ofertas_atuais_banco()
        antes = total_em_tres_redes()
        cont = {
            "lote": lote, "trios_antes": antes,
            "buscas_vtex": 0, "buscas_carrefour": 0,
            "vtex_savegnago": 0, "vtex_atacadao": 0,
            "intersecao_savegnago_atacadao": 0,
            "novos_trios": 0, "precos_adicionados": 0,
            "erros": 0,
        }
        for loja, criar in (
            ("Savegnago", sessao_savegnago),
            ("Atacadão", sessao_atacadao),
        ):
            try:
                sessao = criar(cep)
            except Exception as erro:
                raise CommandError(
                    f"Não foi possível regionalizar {loja}: {erro}"
                ) from erro

            try:
                vistos = set()
                for termo in TERMOS[lote]:
                    cont["buscas_vtex"] += 1
                    try:
                        ofertas = buscar_paginado(
                            loja, termo, sessao, paginas=paginas, tamanho=tamanho
                        )
                    except Exception as erro:
                        cont["erros"] += 1
                        self.stderr.write(
                            f"[expansao] Falha VTEX {loja} {termo}: {erro}"
                        )
                        continue
                    for ean, oferta in ofertas.items():
                        vistos.add(ean)
                        dados[ean][loja] = oferta
                    self.stdout.write(
                        f"[expansao] {loja} {termo}: {len(ofertas)} ofertas, "
                        f"{len(vistos)} EANs únicos."
                    )
                cont["vtex_savegnago" if loja == "Savegnago"
                     else "vtex_atacadao"] = len(vistos)
            finally:
                sessao.close()

        cruzados = {
            ean: ofertas for ean, ofertas in dados.items()
            if "Savegnago" in ofertas and "Atacadão" in ofertas
        }
        cont["intersecao_savegnago_atacadao"] = len(cruzados)
        self.stdout.write(
            f"[expansao] Interseção real Savegnago+Atacadão: "
            f"{len(cruzados)} EANs."
        )
        if not cruzados:
            self.stdout.write(
                "[expansao] Nenhum EAN compartilhado. Não criar ofertas."
            )
            self.stdout.write("[expansao] RESULTADO " + json.dumps(cont))
            return

        # As buscas Carrefour são direcionadas aos EANs já encontrados nas
        # duas outras redes. Nunca importamos produtos soltos da terceira.
        faltando = {
            ean: ofertas for ean, ofertas in cruzados.items()
            if "Carrefour" not in ofertas
        }
        marcas = Counter(
            str(ofertas["Savegnago"]["marca"] or
                ofertas["Atacadão"]["marca"]).strip().casefold()
            for ofertas in faltando.values()
        )
        consultas = [
            marca for marca, _ in marcas.most_common(max_buscas // 2)
            if len(marca) >= 3
        ]
        consultas.extend(CARREFOUR_SEMENTES[lote])
        # Usa buscas gerais e marcas; evita consumir todo o limite numa
        # lista muito grande de marcas pouco frequentes.
        consultas.extend(
            marca for marca, _ in marcas.most_common()
            if len(marca) >= 3
        )
        consultas = list(dict.fromkeys(consultas))
        for termo in consultas[:max_buscas]:
            cont["buscas_carrefour"] += 1
            try:
                produtos = buscar_carrefour(termo=termo, quantidade=itens)
            except Exception as erro:
                cont["erros"] += 1
                self.stderr.write(
                    f"[expansao] Falha Carrefour {termo}: {erro}"
                )
                continue
            for bruto in produtos:
                oferta = normalizar_oferta(bruto, "Carrefour")
                if oferta and oferta["ean"] in cruzados:
                    cruzados[oferta["ean"]]["Carrefour"] = oferta
            self.stdout.write(
                f"[expansao] Carrefour {termo}: "
                f"{sum('Carrefour' in o for o in cruzados.values())} "
                f"EANs nas 3 redes."
            )

        for ean, ofertas in cruzados.items():
            if not all(loja in ofertas for loja in LOJAS):
                continue
            if options["gravar"]:
                try:
                    novos = salvar_trio(ean, ofertas)
                except Exception as erro:
                    cont["erros"] += 1
                    self.stderr.write(
                        f"[expansao] Erro ao gravar EAN {ean}: {erro}"
                    )
                    continue
                cont["precos_adicionados"] += novos
            self.stdout.write(
                f"[expansao] TRIO {ean} | "
                + " | ".join(
                    f"{loja} R$ {ofertas[loja]['valor']}"
                    for loja in LOJAS
                )
            )

        depois = total_em_tres_redes()
        cont["novos_trios"] = max(0, depois - antes) if options["gravar"] else 0
        cont["trios_depois"] = depois
        self.stdout.write(
            "[expansao] RESULTADO " +
            json.dumps(cont, ensure_ascii=False, sort_keys=True)
        )
        if not options["gravar"]:
            self.stdout.write("[expansao] SIMULAÇÃO; banco não alterado.")

"""Encontra produtos com preços verificados nas três redes por EAN.

Descobre a interseção Savegnago x Atacadão em memória e só persiste novas
ofertas se o mesmo EAN também for encontrado no Carrefour. Não cria produtos
soltos nem compara itens somente por nomes parecidos.
"""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from catalogo.models import Produto, Supermercado
from coleta.atacadao import buscar_produtos as buscar_atacadao
from coleta.carrefour import buscar_produtos as buscar_carrefour
from coleta.savegnago import buscar_produtos as buscar_savegnago
from precos.models import OfertaFonte, Preco


CEP = "14010000"
TERMOS = (
    "arroz", "feijão", "macarrão", "café", "leite", "detergente",
    "camil", "ypê", "broto legal", "pilão", "galo", "nissin", "marilan",
)
LOJAS = {
    "Savegnago": "https://www.savegnago.com.br",
    "Atacadão": "https://www.atacadao.com.br",
    "Carrefour": "https://mercado.carrefour.com.br",
}


def normalizar_oferta(item, loja):
    """Retorna a oferta somente se EAN, preço, disponibilidade e origem forem válidos."""
    if not isinstance(item, dict) or item.get("erro"):
        return None

    ean = str(item.get("codigo_barras") or "").strip()
    nome = str(item.get("nome") or "").strip()
    url = str(item.get("url") or "").strip()
    origem_valida = url.startswith(LOJAS[loja] + "/")
    if loja == "Atacadão":
        origem_valida = origem_valida or url.startswith(
            "https://secure.atacadao.com.br/"
        )
    if (
        not nome or not ean.isdigit() or len(ean) not in (8, 12, 13, 14)
        or item.get("disponivel") is not True
        or not origem_valida
    ):
        return None
    if loja == "Carrefour" and not url.startswith(
        "https://mercado.carrefour.com.br/produto/"
    ):
        return None
    if loja != "Carrefour":
        vendedor = str(item.get("vendedor_nome") or "").upper()
        if loja == "Savegnago" and "SAVEGNAGO" not in vendedor:
            return None
        if loja == "Atacadão" and "ATACADAO" not in vendedor:
            return None

    try:
        valor = Decimal(str(item.get("preco")))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not valor.is_finite() or valor <= 0:
        return None

    imagem = str(item.get("imagem_url") or "").strip()
    if len(imagem) > 200 or not imagem.startswith("https://"):
        imagem = ""

    return {
        "ean": ean,
        "nome": nome[:200],
        "marca": str(item.get("marca") or "").strip()[:100],
        "valor": valor,
        "url": url,
        "sku": str(item.get("sku") or "")[:50],
        "imagem": imagem,
    }


def total_em_tres_redes():
    return (
        Preco.objects.filter(
            oferta_fonte__ativo=True,
            oferta_fonte__supermercado__ativo=True,
        )
        .values("oferta_fonte__produto_id")
        .annotate(redes=Count("oferta_fonte__supermercado_id", distinct=True))
        .filter(redes__gte=3)
        .count()
    )


class Command(BaseCommand):
    help = "Busca e grava somente produtos com preços reais nas três redes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--gravar", action="store_true",
            help="Sem esta opção, a execução é apenas diagnóstico.",
        )
        parser.add_argument(
            "--quantidade", type=int, default=30,
            help="Quantidade máxima por consulta de catálogo (1 a 50).",
        )
        parser.add_argument(
            "--max-marcas", type=int, default=12,
            help="Limite de buscas de marcas no Carrefour (1 a 25).",
        )
        parser.add_argument("--cep", default=CEP)

    def handle(self, *args, **options):
        quantidade = options["quantidade"]
        max_marcas = options["max_marcas"]
        cep = "".join(ch for ch in str(options["cep"]) if ch.isdigit())
        gravar = options["gravar"]
        if not 1 <= quantidade <= 50:
            raise CommandError("--quantidade deve estar entre 1 e 50.")
        if not 1 <= max_marcas <= 25:
            raise CommandError("--max-marcas deve estar entre 1 e 25.")
        if len(cep) != 8:
            raise CommandError("--cep deve conter 8 dígitos.")

        inicio = total_em_tres_redes()
        registros = defaultdict(dict)
        estatisticas = {
            "comparaveis_antes": inicio, "buscas_savegnago": 0,
            "buscas_atacadao": 0, "buscas_carrefour": 0,
            "ean_nas_duas_primeiras": 0, "trios_verificados": 0,
            "produtos_criados": 0, "ofertas_criadas": 0,
            "precos_criados": 0, "falhas_consulta": 0,
        }
        self.stdout.write("[triangulacao] Procurando EANs nas duas primeiras redes.")

        for termo in TERMOS:
            for loja, buscar in (
                ("Savegnago", buscar_savegnago),
                ("Atacadão", buscar_atacadao),
            ):
                estatisticas["buscas_" + (
                    "savegnago" if loja == "Savegnago" else "atacadao"
                )] += 1
                try:
                    resultados = buscar(
                        termo=termo, quantidade=quantidade, cep=cep
                    )
                except Exception as erro:
                    estatisticas["falhas_consulta"] += 1
                    self.stderr.write(
                        f"[triangulacao] Erro ao consultar {loja} ({termo}): {erro}"
                    )
                    continue
                for item in resultados:
                    oferta = normalizar_oferta(item, loja)
                    if oferta:
                        registros[oferta["ean"]][loja] = oferta

            encontrados = sum(
                1 for ofertas in registros.values()
                if "Savegnago" in ofertas and "Atacadão" in ofertas
            )
            self.stdout.write(
                f"[triangulacao] {termo}: {encontrados} EANs em ambas as redes."
            )

        candidatos = {
            ean: ofertas for ean, ofertas in registros.items()
            if "Savegnago" in ofertas and "Atacadão" in ofertas
        }
        estatisticas["ean_nas_duas_primeiras"] = len(candidatos)

        # Preços Carrefour já registrados no dia também são ofertas reais.
        # Não os reaproveitamos quando estão com mais de 24 horas.
        limite_recencia = timezone.now() - timedelta(hours=24)
        eans_candidatos = set(candidatos)
        existentes = {}
        if eans_candidatos:
            for oferta in (
                OfertaFonte.objects.filter(
                    produto__codigo_barras__in=eans_candidatos,
                    supermercado__nome__iexact="Carrefour",
                    ativo=True,
                )
                .select_related("produto")
            ):
                preco = oferta.precos.order_by("-data_hora_coleta", "-id").first()
                if preco is not None and preco.data_hora_coleta >= limite_recencia:
                    existentes[oferta.produto.codigo_barras] = {
                        "ean": oferta.produto.codigo_barras,
                        "nome": oferta.produto.nome,
                        "marca": oferta.produto.marca,
                        "valor": preco.valor,
                        "url": oferta.url_fonte,
                        "sku": oferta.codigo_externo,
                        "imagem": oferta.produto.imagem_url or "",
                    }

        marcas_busca = {}
        for ean, ofertas in candidatos.items():
            if ean in existentes:
                ofertas["Carrefour"] = existentes[ean]
                continue
            origem = ofertas["Savegnago"]
            marca = origem["marca"] or ofertas["Atacadão"]["marca"]
            termo = marca.strip() if len(marca.strip()) >= 3 else origem["nome"].split()[0]
            marcas_busca.setdefault(termo.casefold(), []).append(ean)

        self.stdout.write(
            f"[triangulacao] {len(candidatos)} EANs candidatos; "
            f"{len(existentes)} com preço Carrefour recente já registrado."
        )

        for termo, eans in list(marcas_busca.items())[:max_marcas]:
            estatisticas["buscas_carrefour"] += 1
            try:
                resultados = buscar_carrefour(
                    termo=termo, quantidade=min(quantidade, 20)
                )
            except Exception as erro:
                estatisticas["falhas_consulta"] += 1
                self.stderr.write(
                    f"[triangulacao] Erro ao consultar Carrefour ({termo}): {erro}"
                )
                continue
            for item in resultados:
                oferta = normalizar_oferta(item, "Carrefour")
                if oferta and oferta["ean"] in eans:
                    candidatos[oferta["ean"]]["Carrefour"] = oferta

        trios = [
            ofertas for ofertas in candidatos.values()
            if all(loja in ofertas for loja in LOJAS)
        ]
        estatisticas["trios_verificados"] = len(trios)
        self.stdout.write(
            f"[triangulacao] {len(trios)} EANs verificados nas 3 redes."
        )

        if gravar:
            for ofertas in trios:
                try:
                    with transaction.atomic():
                        primeiro = ofertas["Savegnago"]
                        produto = Produto.objects.filter(
                            codigo_barras=primeiro["ean"]
                        ).first()
                        if produto is None:
                            produto = Produto.objects.create(
                                codigo_barras=primeiro["ean"],
                                nome=primeiro["nome"],
                                marca=primeiro["marca"],
                                imagem_url=primeiro["imagem"] or None,
                            )
                            estatisticas["produtos_criados"] += 1

                        for loja in LOJAS:
                            item = ofertas[loja]
                            supermercado, _ = Supermercado.objects.get_or_create(
                                nome=loja,
                                defaults={
                                    "endereco": "", "complemento": "",
                                    "cidade": "Ribeirão Preto",
                                    "estado": "SP", "site_url": LOJAS[loja],
                                    "ativo": True,
                                },
                            )
                            oferta = OfertaFonte.objects.filter(
                                produto=produto,
                                supermercado=supermercado,
                                ativo=True,
                            ).first()
                            if oferta is None:
                                if OfertaFonte.objects.filter(
                                    produto=produto, supermercado=supermercado
                                ).exists():
                                    raise ValueError(
                                        "Oferta inativa: não reativar automaticamente."
                                    )
                                oferta = OfertaFonte.objects.create(
                                    produto=produto, supermercado=supermercado,
                                    codigo_externo=item["sku"],
                                    nome_externo=item["nome"],
                                    url_fonte=item["url"],
                                    ativo=True,
                                )
                                estatisticas["ofertas_criadas"] += 1
                            anterior = oferta.precos.order_by(
                                "-data_hora_coleta", "-id"
                            ).first()
                            if anterior is None or anterior.valor != item["valor"]:
                                Preco.objects.create(
                                    oferta_fonte=oferta,
                                    valor=item["valor"],
                                    data_hora_coleta=timezone.now(),
                                )
                                estatisticas["precos_criados"] += 1
                except Exception as erro:
                    self.stderr.write(
                        f"[triangulacao] Falha ao gravar EAN "
                        f"{ofertas['Savegnago']['ean']}: {erro}"
                    )

        estatisticas["comparaveis_depois"] = total_em_tres_redes()
        self.stdout.write(
            "[triangulacao] RESULTADO " +
            json.dumps(estatisticas, ensure_ascii=False, sort_keys=True)
        )
        if not gravar:
            self.stdout.write(
                "[triangulacao] SIMULAÇÃO: nenhum dado foi gravado."
            )
        if not trios:
            self.stderr.write(
                "[triangulacao] Nenhum produto nas 3 redes encontrado nesta "
                "amostra. Não criar preços fictícios."
            )

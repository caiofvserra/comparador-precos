from decimal import Decimal, InvalidOperation

import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalogo.models import Produto, Supermercado
from precos.models import OfertaFonte, Preco
from coleta.savegnago import buscar_produtos


class Command(BaseCommand):
    help = "Importa produtos e preços do Savegnago, com simulação por padrão."

    def add_arguments(self, parser):
        parser.add_argument("--termo", default="feijão")
        parser.add_argument("--quantidade", type=int, default=10)
        parser.add_argument("--cep", default="14010000")
        parser.add_argument(
            "--gravar",
            action="store_true",
            help="Grava os produtos, ofertas e preços no banco.",
        )

    def handle(self, *args, **options):
        termo = options["termo"]
        quantidade = options["quantidade"]
        cep = "".join(c for c in options["cep"] if c.isdigit())
        gravar = options["gravar"]

        if len(cep) != 8:
            self.stderr.write(self.style.ERROR("Informe um CEP válido com 8 dígitos."))
            return

        if not 1 <= quantidade <= 50:
            self.stderr.write(self.style.ERROR("A quantidade deve estar entre 1 e 50."))
            return

        supermercado = Supermercado.objects.filter(
            nome__iexact="Savegnago", ativo=True
        ).first()

        if supermercado is None:
            self.stderr.write(self.style.ERROR("Savegnago não está cadastrado como ativo."))
            return

        self.stdout.write(f"Consultando Savegnago para o CEP {cep}...")

        try:
            itens = buscar_produtos(termo=termo, quantidade=quantidade, cep=cep)
        except (requests.RequestException, ValueError) as erro:
            self.stderr.write(self.style.ERROR(f"Falha na consulta: {erro}"))
            return

        self.stdout.write(
            self.style.WARNING(
                "MODO DE GRAVAÇÃO" if gravar
                else "MODO SIMULAÇÃO: nenhum dado será gravado."
            )
        )

        contagem = {
            "consultados": len(itens),
            "invalidos": 0,
            "indisponiveis": 0,
            "precos_invalidos": 0,
            "produtos_novos": 0,
            "ofertas_novas": 0,
            "ofertas_existentes": 0,
            "precos_gravados": 0,
            "precos_inalterados": 0,
        }

        agora = timezone.now()

        try:
            with transaction.atomic():
                for item in itens:
                    nome = (item.get("nome") or "").strip()
                    marca = (item.get("marca") or "").strip()
                    ean = (item.get("codigo_barras") or "").strip()
                    url = (item.get("url") or "").strip()

                    vendedor_id = (item.get("vendedor_id") or "").strip()
                    vendedor_nome = (
                        item.get("vendedor_nome") or ""
                    ).strip().upper()

                    if (
                        not nome
                        or not ean.isdigit()
                        or len(ean) not in (8, 12, 13, 14)
                        or not url.startswith("https://www.savegnago.com.br/")
                        or not vendedor_id
                        or "SAVEGNAGO" not in vendedor_nome
                    ):
                        contagem["invalidos"] += 1
                        self.stdout.write(
                            f"IGNORADO — dados, EAN ou vendedor inválidos: {nome}"
                        )
                        continue

                    if not item.get("disponivel"):
                        contagem["indisponiveis"] += 1
                        self.stdout.write(f"INDISPONÍVEL — {nome}")
                        continue

                    try:
                        preco = Decimal(str(item.get("preco")))
                        if not preco.is_finite() or preco <= 0:
                            raise InvalidOperation
                    except (InvalidOperation, TypeError, ValueError):
                        contagem["precos_invalidos"] += 1
                        self.stdout.write(f"IGNORADO — preço inválido: {nome}")
                        continue

                    produto = Produto.objects.filter(codigo_barras=ean).first()
                    oferta = None

                    if produto:
                        oferta = OfertaFonte.objects.filter(
                            produto=produto,
                            supermercado=supermercado,
                            ativo=True,
                        ).first()
                        self.stdout.write(f"PRODUTO EXISTENTE — {produto.nome}")
                    else:
                        contagem["produtos_novos"] += 1
                        self.stdout.write(f"PRODUTO NOVO — {nome} | EAN {ean}")

                    if oferta:
                        contagem["ofertas_existentes"] += 1
                        self.stdout.write(f"OFERTA EXISTENTE — {nome}")

                        ultimo_preco = oferta.precos.order_by(
                            "-data_hora_coleta"
                        ).first()

                        if ultimo_preco and ultimo_preco.valor == preco:
                            contagem["precos_inalterados"] += 1
                            self.stdout.write(
                                f"PREÇO SEM ALTERAÇÃO — R$ {preco:.2f}"
                            )
                            continue
                    else:
                        contagem["ofertas_novas"] += 1
                        self.stdout.write(f"NOVA OFERTA — {nome}")

                    self.stdout.write(f"PREÇO CONSULTADO — R$ {preco:.2f}")

                    if not gravar:
                        continue

                    if produto is None:
                        produto = Produto.objects.create(
                            nome=nome,
                            marca=marca,
                            codigo_barras=ean,
                        )

                    if oferta is None:
                        oferta = OfertaFonte(
                            produto=produto,
                            supermercado=supermercado,
                            codigo_externo=str(item.get("sku") or "")[:50],
                            nome_externo=nome[:200],
                            url_fonte=url,
                            ativo=True,
                        )
                        oferta.save()

                    ultimo_preco = oferta.precos.order_by(
                        "-data_hora_coleta"
                    ).first()

                    if ultimo_preco and ultimo_preco.valor == preco:
                        self.stdout.write(
                            f"PREÇO SEM ALTERAÇÃO — R$ {preco:.2f}"
                        )
                        continue

                    Preco.objects.create(
                        oferta_fonte=oferta,
                        valor=preco,
                        data_hora_coleta=agora,
                    )
                    contagem["precos_gravados"] += 1

                if not gravar:
                    transaction.set_rollback(True)

        except Exception as erro:
            self.stderr.write(
                self.style.ERROR(f"Importação cancelada; transação revertida: {erro}")
            )
            return

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Produtos consultados: {contagem['consultados']}")
        self.stdout.write(f"Dados ou EANs inválidos: {contagem['invalidos']}")
        self.stdout.write(f"Indisponíveis: {contagem['indisponiveis']}")
        self.stdout.write(f"Preços inválidos: {contagem['precos_invalidos']}")
        self.stdout.write(f"Produtos novos identificados: {contagem['produtos_novos']}")
        self.stdout.write(f"Ofertas novas identificadas: {contagem['ofertas_novas']}")
        self.stdout.write(f"Ofertas existentes: {contagem['ofertas_existentes']}")
        self.stdout.write(f"Preços gravados: {contagem['precos_gravados']}")
        self.stdout.write(f"Preços sem alteração: {contagem['precos_inalterados']}")

        if gravar:
            self.stdout.write(self.style.SUCCESS("Importação concluída."))
        else:
            self.stdout.write(self.style.WARNING("Simulação concluída; banco inalterado."))

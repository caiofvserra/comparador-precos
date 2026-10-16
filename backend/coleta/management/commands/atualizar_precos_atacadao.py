
from decimal import Decimal, InvalidOperation

import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from precos.models import OfertaFonte, Preco
from coleta.atacadao import criar_sessao, URL_BUSCA


class Command(BaseCommand):
    help = "Atualiza preços das ofertas existentes do Atacadão."

    def add_arguments(self, parser):
        parser.add_argument("--cep", default="14010000")
        parser.add_argument(
            "--gravar",
            action="store_true",
            help="Grava os novos preços no banco.",
        )

    def handle(self, *args, **options):
        cep = "".join(c for c in options["cep"] if c.isdigit())
        gravar = options["gravar"]

        if len(cep) != 8:
            self.stderr.write(self.style.ERROR("CEP inválido."))
            return

        ofertas = list(
            OfertaFonte.objects.filter(
                supermercado__nome__iexact="Atacadão",
                supermercado__ativo=True,
                ativo=True,
            ).select_related("produto", "supermercado")
        )

        self.stdout.write(f"Ofertas para verificar: {len(ofertas)}")
        self.stdout.write(f"CEP: {cep}")
        self.stdout.write(self.style.WARNING(
            "MODO GRAVAÇÃO" if gravar
            else "SIMULAÇÃO: banco não será alterado."
        ))

        try:
            sessao = criar_sessao(cep)
        except (requests.RequestException, ValueError) as erro:
            self.stderr.write(self.style.ERROR(
                f"Não foi possível criar sessão: {erro}"
            ))
            return

        contagem = {
            "consultadas": 0,
            "sem_sku": 0,
            "nao_encontradas": 0,
            "ean_divergente": 0,
            "indisponiveis": 0,
            "preco_invalido": 0,
            "inalterados": 0,
            "alteracoes": 0,
            "gravados": 0,
            "falhas": 0,
        }

        agora = timezone.now()

        for oferta in ofertas:
            produto = oferta.produto
            sku = (oferta.codigo_externo or "").strip()

            if not sku:
                contagem["sem_sku"] += 1
                self.stdout.write(f"SEM SKU — {produto.nome}")
                continue

            try:
                resposta = sessao.get(
                    URL_BUSCA,
                    params={
                        "fq": f"skuId:{sku}",
                        "_from": 0,
                        "_to": 0,
                    },
                    timeout=30,
                )
                resposta.raise_for_status()
                resultados = resposta.json()

                if not isinstance(resultados, list):
                    raise ValueError("Resposta inesperada da API.")

            except (requests.RequestException, ValueError) as erro:
                contagem["falhas"] += 1
                self.stdout.write(
                    f"FALHA NA CONSULTA — {produto.nome}: {erro}"
                )
                continue

            contagem["consultadas"] += 1
            encontrado = None
            item_encontrado = None
            vendedor_encontrado = None

            for resultado in resultados:
                for item in resultado.get("items") or []:
                    if str(item.get("itemId") or "").strip() != sku:
                        continue

                    ean_site = str(item.get("ean") or "").strip()
                    ean_banco = str(produto.codigo_barras or "").strip()

                    if ean_site == "0":
                        ean_site = ""

                    if ean_banco and ean_site != ean_banco:
                        continue

                    vendedor = next(
                        (
                            v for v in item.get("sellers") or []
                            if "ATACADAO" in str(
                                v.get("sellerName") or ""
                            ).upper()
                        ),
                        None,
                    )

                    if vendedor is not None:
                        encontrado = resultado
                        item_encontrado = item
                        vendedor_encontrado = vendedor
                        break

                if encontrado is not None:
                    break

            if encontrado is None:
                sku_encontrado = any(
                    str(item.get("itemId") or "").strip() == sku
                    for resultado in resultados
                    for item in (resultado.get("items") or [])
                )

                if sku_encontrado and produto.codigo_barras:
                    contagem["ean_divergente"] += 1
                    self.stdout.write(
                        f"EAN DIVERGENTE — {produto.nome} | SKU {sku}"
                    )
                else:
                    contagem["nao_encontradas"] += 1
                    self.stdout.write(
                        f"SKU NÃO ENCONTRADO — {produto.nome} | SKU {sku}"
                    )
                continue

            comercial = (
                vendedor_encontrado.get("commertialOffer") or {}
            )

            if (
                not comercial.get("IsAvailable", False)
                or comercial.get("AvailableQuantity", 0) <= 0
            ):
                contagem["indisponiveis"] += 1
                self.stdout.write(f"INDISPONÍVEL — {produto.nome}")
                continue

            try:
                preco = Decimal(str(comercial.get("Price")))
                if not preco.is_finite() or preco <= 0:
                    raise InvalidOperation
            except (InvalidOperation, TypeError, ValueError):
                contagem["preco_invalido"] += 1
                self.stdout.write(f"PREÇO INVÁLIDO — {produto.nome}")
                continue

            ultimo = oferta.precos.order_by(
                "-data_hora_coleta"
            ).first()

            if ultimo and ultimo.valor == preco:
                contagem["inalterados"] += 1
                self.stdout.write(
                    f"SEM ALTERAÇÃO — {produto.nome} | R$ {preco:.2f}"
                )
                continue

            contagem["alteracoes"] += 1
            self.stdout.write(
                f"{'ATUALIZAR' if gravar else 'SIMULAR'} — "
                f"{produto.nome} | "
                f"{'sem histórico' if ultimo is None else f'R$ {ultimo.valor:.2f}'}"
                f" -> R$ {preco:.2f}"
            )

            if gravar:
                with transaction.atomic():
                    Preco.objects.create(
                        oferta_fonte=oferta,
                        valor=preco,
                        data_hora_coleta=agora,
                    )
                contagem["gravados"] += 1

        self.stdout.write("")
        self.stdout.write("=" * 48)

        for chave, valor in contagem.items():
            self.stdout.write(f"{chave}: {valor}")

        if gravar:
            self.stdout.write(self.style.SUCCESS(
                "Atualização concluída."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "Simulação concluída; banco inalterado."
            ))

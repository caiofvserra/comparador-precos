
from decimal import Decimal, InvalidOperation
import re
import unicodedata

import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from catalogo.models import Produto, Supermercado
from precos.models import OfertaFonte, Preco
from coleta.atacadao import criar_sessao, URL_BUSCA


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto or "").casefold())
    texto = "".join(
        c for c in texto if not unicodedata.combining(c)
    )
    return " ".join(re.findall(r"[a-z0-9]+", texto))


def palavras_busca(produto):
    nome = normalizar(produto.nome)
    marca = normalizar(produto.marca)
    termos = []

    # A marca ajuda a refinar a busca sem depender dela para validar o EAN.
    if marca:
        termos.append(f"{marca} {nome}".strip())

    termos.append(nome)

    # Evita repetir consultas iguais.
    return list(dict.fromkeys(t for t in termos if t))


class Command(BaseCommand):
    help = (
        "Concilia produtos do Savegnago com o Atacadão "
        "por EAN exato, em simulação por padrão."
    )

    def add_arguments(self, parser):
        parser.add_argument("--cep", default="14010000")
        parser.add_argument(
            "--quantidade",
            type=int,
            default=20,
            help="Máximo de resultados consultados por busca (1 a 50).",
        )
        parser.add_argument(
            "--limite",
            type=int,
            default=0,
            help="Limita o número de produtos processados; 0 significa todos.",
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Número de produtos a pular na lista ordenada.",
        )
        parser.add_argument(
            "--gravar",
            action="store_true",
            help="Grava ofertas e preços iniciais das correspondências exatas.",
        )

    def handle(self, *args, **options):
        cep = "".join(c for c in options["cep"] if c.isdigit())
        quantidade = options["quantidade"]
        limite = options["limite"]
        offset = options["offset"]
        gravar = options["gravar"]

        if len(cep) != 8:
            self.stderr.write(self.style.ERROR("CEP inválido."))
            return

        if not 1 <= quantidade <= 50:
            self.stderr.write(
                self.style.ERROR("--quantidade deve estar entre 1 e 50.")
            )
            return

        if limite < 0:
            self.stderr.write(
                self.style.ERROR("--limite não pode ser negativo.")
            )
            return

        if offset < 0:
            self.stderr.write(
                self.style.ERROR("--offset não pode ser negativo.")
            )
            return

        savegnago = Supermercado.objects.filter(
            nome__iexact="Savegnago",
            ativo=True,
        ).first()

        atacadao = Supermercado.objects.filter(
            nome__iexact="Atacadão",
            ativo=True,
        ).first()

        if not savegnago:
            self.stderr.write(
                self.style.ERROR("Supermercado Savegnago ativo não encontrado.")
            )
            return

        if not atacadao:
            self.stderr.write(
                self.style.ERROR("Supermercado Atacadão ativo não encontrado.")
            )
            return

        ofertas_atacadao_ativas = OfertaFonte.objects.filter(
            produto_id=OuterRef("pk"),
            supermercado=atacadao,
            ativo=True,
        )

        produtos = list(
            Produto.objects.filter(
                ofertas__supermercado=savegnago,
                ofertas__ativo=True,
            )
            .distinct()
            .order_by("nome")
        )

        if offset:
            produtos = produtos[offset:]

        if limite:
            produtos = produtos[:limite]

        produtos = [
            produto
            for produto in produtos
            if not OfertaFonte.objects.filter(
                produto=produto,
                supermercado=atacadao,
                ativo=True,
            ).exists()
        ]

        self.stdout.write(f"Produtos do Savegnago a conciliar: {len(produtos)}")
        self.stdout.write(f"CEP regional: {cep}")
        self.stdout.write(
            self.style.WARNING(
                "MODO GRAVAÇÃO" if gravar
                else "SIMULAÇÃO: banco não será alterado."
            )
        )

        try:
            sessao = criar_sessao(cep)
        except (requests.RequestException, ValueError) as erro:
            self.stderr.write(
                self.style.ERROR(f"Falha ao criar sessão do Atacadão: {erro}")
            )
            return

        contagem = {
            "produtos_processados": 0,
            "sem_ean": 0,
            "sem_resultados": 0,
            "ean_nao_encontrado": 0,
            "indisponiveis": 0,
            "preco_invalido": 0,
            "correspondencias_exatas": 0,
            "ofertas_ja_existentes": 0,
            "ofertas_novas": 0,
            "precos_iniciais_gravados": 0,
            "falhas_consulta": 0,
        }

        agora = timezone.now()

        for produto in produtos:
            contagem["produtos_processados"] += 1
            ean = str(produto.codigo_barras or "").strip()

            if not ean.isdigit() or len(ean) not in (8, 12, 13, 14):
                contagem["sem_ean"] += 1
                self.stdout.write(f"SEM EAN VÁLIDO — {produto.nome}")
                continue

            oferta_existente = OfertaFonte.objects.filter(
                produto=produto,
                supermercado=atacadao,
                ativo=True,
            ).first()

            resultados_por_id = {}
            consulta_falhou = False

            for termo in palavras_busca(produto):
                try:
                    resposta = sessao.get(
                        URL_BUSCA,
                        params={
                            "ft": termo,
                            "_from": 0,
                            "_to": quantidade - 1,
                        },
                        timeout=30,
                    )
                    resposta.raise_for_status()
                    dados = resposta.json()

                    if not isinstance(dados, list):
                        raise ValueError("Formato inesperado da API.")

                    for resultado in dados:
                        identificador = str(
                            resultado.get("productId") or ""
                        ).strip()
                        if identificador:
                            resultados_por_id[identificador] = resultado

                except (requests.RequestException, ValueError) as erro:
                    consulta_falhou = True
                    self.stdout.write(
                        f"FALHA NA BUSCA — {produto.nome} | {erro}"
                    )
                    break

            if consulta_falhou:
                contagem["falhas_consulta"] += 1
                continue

            if not resultados_por_id:
                contagem["sem_resultados"] += 1
                self.stdout.write(f"NENHUM RESULTADO — {produto.nome}")
                continue

            candidatos = []

            for resultado in resultados_por_id.values():
                for item in resultado.get("items") or []:
                    ean_site = str(item.get("ean") or "").strip()

                    if ean_site == "0":
                        ean_site = ""

                    if ean_site != ean:
                        continue

                    sku = str(item.get("itemId") or "").strip()
                    if not sku:
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

                    if vendedor is None:
                        continue

                    candidatos.append((resultado, item, vendedor))

            if not candidatos:
                contagem["ean_nao_encontrado"] += 1
                self.stdout.write(
                    f"SEM CORRESPONDÊNCIA EXATA — {produto.nome} | EAN {ean}"
                )
                continue

            # Escolhe apenas uma oferta disponível, com preço válido.
            escolhido = None
            preco_escolhido = None

            for resultado, item, vendedor in candidatos:
                comercial = vendedor.get("commertialOffer") or {}

                if (
                    not comercial.get("IsAvailable", False)
                    or comercial.get("AvailableQuantity", 0) <= 0
                ):
                    continue

                try:
                    preco = Decimal(str(comercial.get("Price")))
                    if not preco.is_finite() or preco <= 0:
                        raise InvalidOperation
                except (InvalidOperation, TypeError, ValueError):
                    continue

                escolhido = (resultado, item, vendedor)
                preco_escolhido = preco
                break

            if escolhido is None:
                # Diferencia indisponibilidade de preço inválido.
                tem_disponivel = any(
                    (v.get("commertialOffer") or {}).get(
                        "IsAvailable", False
                    )
                    and (v.get("commertialOffer") or {}).get(
                        "AvailableQuantity", 0
                    ) > 0
                    for _, _, v in candidatos
                )

                if tem_disponivel:
                    contagem["preco_invalido"] += 1
                    self.stdout.write(f"PREÇO INVÁLIDO — {produto.nome}")
                else:
                    contagem["indisponiveis"] += 1
                    self.stdout.write(f"INDISPONÍVEL — {produto.nome}")
                continue

            resultado, item, vendedor = escolhido
            nome_externo = (
                resultado.get("productName") or produto.nome
            ).strip()
            url = (resultado.get("link") or "").strip()

            if not (
                url.startswith("https://www.atacadao.com.br/")
                or url.startswith("https://secure.atacadao.com.br/")
            ):
                contagem["falhas_consulta"] += 1
                self.stdout.write(f"URL INVÁLIDA — {produto.nome}")
                continue

            sku = str(item.get("itemId") or "").strip()
            contagem["correspondencias_exatas"] += 1

            if oferta_existente:
                contagem["ofertas_ja_existentes"] += 1
                self.stdout.write(
                    f"OFERTA JÁ EXISTE — {produto.nome} | "
                    f"SKU {oferta_existente.codigo_externo}"
                )
                continue

            contagem["ofertas_novas"] += 1
            self.stdout.write(
                f"{'CRIAR' if gravar else 'SIMULAR OFERTA'} — {produto.nome}\n"
                f"  EAN: {ean} | SKU Atacadão: {sku}\n"
                f"  Produto no site: {nome_externo}\n"
                f"  Preço Atacadão: R$ {preco_escolhido:.2f}\n"
                f"  URL: {url}"
            )

            if not gravar:
                continue

            try:
                with transaction.atomic():
                    oferta = OfertaFonte(
                        produto=produto,
                        supermercado=atacadao,
                        codigo_externo=sku[:50],
                        nome_externo=nome_externo[:200],
                        url_fonte=url,
                        ativo=True,
                    )
                    oferta.save()

                    Preco.objects.create(
                        oferta_fonte=oferta,
                        valor=preco_escolhido,
                        data_hora_coleta=agora,
                    )

                contagem["precos_iniciais_gravados"] += 1

            except Exception as erro:
                contagem["falhas_consulta"] += 1
                self.stdout.write(
                    f"FALHA AO GRAVAR — {produto.nome}: {erro}"
                )

        self.stdout.write("")
        self.stdout.write("=" * 55)

        for chave, valor in contagem.items():
            self.stdout.write(f"{chave}: {valor}")

        if gravar:
            self.stdout.write(
                self.style.SUCCESS("Conciliação concluída.")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Simulação concluída; banco inalterado."
                )
            )

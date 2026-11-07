from decimal import Decimal
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase

from catalogo.models import Produto, Supermercado
from coleta.vtex_paginado import extrair_skus, buscar_paginado
from precos.models import OfertaFonte, Preco


EAN = "7896003740240"
OUTRO = "7898080640765"


def produto_vtex(nome="Biscoito Marilan", ean=EAN, variantes=False):
    indisponivel = {
        "ean": OUTRO, "name": "Outra variante",
        "itemId": "bad",
        "sellers": [{
            "sellerName": "ATACADAO",
            "commertialOffer": {
                "IsAvailable": False, "AvailableQuantity": 0, "Price": 1.00
            },
        }],
    }
    disponivel = {
        "ean": ean, "name": nome + " 300g", "itemId": "sku2",
        "images": [{"imageUrl": "https://example.com/img.jpg"}],
        "sellers": [{
            "sellerName": "ATACADAO",
            "commertialOffer": {
                "IsAvailable": True, "AvailableQuantity": 8, "Price": 4.89
            },
        }],
    }
    return {
        "productName": nome, "brand": "Marilan",
        "link": "https://www.atacadao.com.br/biscoito/p",
        "items": [indisponivel, disponivel] if variantes else [disponivel],
    }


class VtexPaginadoTests(TestCase):
    def test_le_todas_variantes_e_rejeita_indisponivel(self):
        produtos = extrair_skus([produto_vtex(variantes=True)], "Atacadão")
        self.assertEqual(list(produtos), [EAN])
        self.assertEqual(produtos[EAN]["valor"], Decimal("4.89"))
        self.assertEqual(produtos[EAN]["sku"], "sku2")

    def test_varre_mais_de_uma_pagina(self):
        resposta1 = Mock(status_code=200)
        resposta1.json.return_value = [
            produto_vtex(ean=EAN),
            produto_vtex(ean=OUTRO),
        ]
        resposta2 = Mock(status_code=200)
        resposta2.json.return_value = [
            produto_vtex(ean="7891234567895")
        ]
        sessao = Mock()
        sessao.get.side_effect = [resposta1, resposta2]
        produtos = buscar_paginado(
            "Atacadão", "biscoito", sessao, paginas=2, tamanho=2
        )
        self.assertEqual(len(produtos), 3)
        self.assertEqual(sessao.get.call_count, 2)

    def test_aceita_vendedor_com_acento_e_dominio_sem_www(self):
        bruto = produto_vtex()
        bruto["items"][0]["sellers"][0]["sellerName"] = "Atacadão"
        bruto["link"] = "https://atacadao.com.br/biscoito/p"
        produtos = extrair_skus([bruto], "Atacadão")
        self.assertEqual(list(produtos), [EAN])
        self.assertEqual(produtos[EAN]["url"],
                         "https://www.atacadao.com.br/biscoito/p")

    def test_nao_aceita_vendedor_diferente(self):
        bruto = produto_vtex()
        bruto["items"][0]["sellers"][0]["sellerName"] = "OUTRA LOJA"
        self.assertEqual(extrair_skus([bruto], "Atacadão"), {})


def oferta(loja, ean=EAN):
    return {
        "ean": ean,
        "nome": "Biscoito Marilan 300g",
        "marca": "Marilan",
        "valor": Decimal({
            "Savegnago": "4.98",
            "Atacadão": "4.89",
            "Carrefour": "6.99",
        }[loja]),
        "sku": "sku-123",
        "url": {
            "Savegnago": "https://www.savegnago.com.br/biscoito/p",
            "Atacadão": "https://www.atacadao.com.br/biscoito/p",
            "Carrefour": "https://mercado.carrefour.com.br/produto/biscoito",
        }[loja],
        "imagem": "",
    }


def carrefour_bruto(ean=EAN):
    return {
        "codigo_barras": ean,
        "nome": "Biscoito Marilan 300g",
        "marca": "Marilan",
        "preco": "6.99",
        "sku": "sku-123",
        "url": "https://mercado.carrefour.com.br/produto/biscoito",
        "disponivel": True,
    }


class ExpandirTriosTests(TestCase):
    @patch("coleta.management.commands.expandir_trios.sessao_atacadao")
    @patch("coleta.management.commands.expandir_trios.sessao_savegnago")
    @patch("coleta.management.commands.expandir_trios.buscar_paginado")
    @patch("coleta.management.commands.expandir_trios.buscar_carrefour")
    def test_so_grava_trios_e_execucao_e_idempotente(
        self, carrefour, vtex, sessao_save, sessao_atac,
    ):
        def fake_buscar(loja, termo, sessao, paginas, tamanho):
            if termo == "arroz":
                return {EAN: oferta(loja)}
            if termo == "feijão":
                return {OUTRO: oferta(loja, OUTRO)}
            return {}
        vtex.side_effect = fake_buscar
        carrefour.return_value = [carrefour_bruto()]

        call_command(
            "expandir_trios", gravar=True,
            lote=1, paginas=1, tamanho=2, buscas_carrefour=2,
            itens_carrefour=2, stdout=StringIO(),
        )
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(Supermercado.objects.count(), 3)
        self.assertEqual(OfertaFonte.objects.count(), 3)
        self.assertEqual(Preco.objects.count(), 3)

        call_command(
            "expandir_trios", gravar=True,
            lote=1, paginas=1, tamanho=2, buscas_carrefour=2,
            itens_carrefour=2, stdout=StringIO(),
        )
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(Preco.objects.count(), 3)

    @patch("coleta.management.commands.expandir_trios.sessao_atacadao")
    @patch("coleta.management.commands.expandir_trios.sessao_savegnago")
    @patch("coleta.management.commands.expandir_trios.buscar_paginado")
    @patch("coleta.management.commands.expandir_trios.buscar_carrefour")
    def test_nao_cria_nem_par_sem_carrefour(
        self, carrefour, vtex, sessao_save, sessao_atac,
    ):
        vtex.side_effect = (
            lambda loja, termo, sessao, paginas, tamanho:
            {EAN: oferta(loja)} if termo == "arroz" else {}
        )
        carrefour.return_value = []
        call_command(
            "expandir_trios", gravar=True,
            lote=1, paginas=1, tamanho=2, buscas_carrefour=2,
            itens_carrefour=2, stdout=StringIO(),
        )
        self.assertEqual(Produto.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)

    @patch("coleta.management.commands.expandir_trios.sessao_atacadao")
    @patch("coleta.management.commands.expandir_trios.sessao_savegnago")
    @patch("coleta.management.commands.expandir_trios.buscar_paginado")
    @patch("coleta.management.commands.expandir_trios.buscar_carrefour")
    def test_simulacao_nao_altera_banco(
        self, carrefour, vtex, sessao_save, sessao_atac,
    ):
        vtex.side_effect = (
            lambda loja, termo, sessao, paginas, tamanho:
            {EAN: oferta(loja)} if termo == "arroz" else {}
        )
        carrefour.return_value = [carrefour_bruto()]
        call_command(
            "expandir_trios", lote=1, paginas=1, tamanho=2,
            buscas_carrefour=1, itens_carrefour=2, stdout=StringIO(),
        )
        self.assertEqual(Produto.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)

from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from catalogo.models import Produto, Supermercado
from precos.models import OfertaFonte, Preco


EAN = "7896200115346"


def oferta(loja):
    enderecos = {
        "Savegnago": "https://www.savegnago.com.br/produto/p",
        "Atacadão": "https://www.atacadao.com.br/produto/p",
        "Carrefour": "https://mercado.carrefour.com.br/produto/p",
    }
    return {
        "nome": "Feijão carioca marca comum 1kg",
        "marca": "Marca Comum",
        "codigo_barras": EAN,
        "sku": "sku-123",
        "vendedor_nome": {
            "Savegnago": "SAVEGNAGO",
            "Atacadão": "ATACADAO",
            "Carrefour": "",
        }[loja],
        "preco": {
            "Savegnago": "7.20",
            "Atacadão": "6.90",
            "Carrefour": "7.00",
        }[loja],
        "disponivel": True,
        "url": enderecos[loja],
    }


class TriangularPrecosTests(TestCase):
    @patch(
        "coleta.management.commands.triangular_precos.buscar_savegnago"
    )
    @patch(
        "coleta.management.commands.triangular_precos.buscar_atacadao"
    )
    @patch(
        "coleta.management.commands.triangular_precos.buscar_carrefour"
    )
    def test_cadastra_exclusivamente_trio_real_e_nao_duplica_preco(
        self, carrefour, atacadao, savegnago
    ):
        savegnago.side_effect = lambda termo, quantidade, cep: (
            [oferta("Savegnago")] if termo == "feijão" else []
        )
        atacadao.side_effect = lambda termo, quantidade, cep: (
            [oferta("Atacadão")] if termo == "feijão" else []
        )
        carrefour.return_value = [oferta("Carrefour")]

        call_command("triangular_precos", gravar=True, stdout=StringIO())
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(Supermercado.objects.count(), 3)
        self.assertEqual(OfertaFonte.objects.count(), 3)
        self.assertEqual(Preco.objects.count(), 3)
        self.assertEqual(
            set(Preco.objects.values_list("valor", flat=True)),
            {Decimal("7.20"), Decimal("6.90"), Decimal("7.00")},
        )

        call_command("triangular_precos", gravar=True, stdout=StringIO())
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(OfertaFonte.objects.count(), 3)
        self.assertEqual(Preco.objects.count(), 3)

    @patch(
        "coleta.management.commands.triangular_precos.buscar_savegnago"
    )
    @patch(
        "coleta.management.commands.triangular_precos.buscar_atacadao"
    )
    @patch(
        "coleta.management.commands.triangular_precos.buscar_carrefour"
    )
    def test_nao_cadastra_pares_sem_carrefour(
        self, carrefour, atacadao, savegnago
    ):
        savegnago.return_value = [oferta("Savegnago")]
        atacadao.return_value = [oferta("Atacadão")]
        carrefour.return_value = []

        call_command("triangular_precos", gravar=True, stdout=StringIO())
        self.assertEqual(Produto.objects.count(), 0)
        self.assertEqual(OfertaFonte.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)

    @patch(
        "coleta.management.commands.triangular_precos.buscar_savegnago"
    )
    @patch(
        "coleta.management.commands.triangular_precos.buscar_atacadao"
    )
    @patch(
        "coleta.management.commands.triangular_precos.buscar_carrefour"
    )
    def test_simulacao_nao_altera_banco(
        self, carrefour, atacadao, savegnago
    ):
        savegnago.return_value = [oferta("Savegnago")]
        atacadao.return_value = [oferta("Atacadão")]
        carrefour.return_value = [oferta("Carrefour")]

        call_command("triangular_precos", stdout=StringIO())
        self.assertEqual(Produto.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)

    @patch(
        "coleta.management.commands.triangular_precos.buscar_savegnago"
    )
    @patch(
        "coleta.management.commands.triangular_precos.buscar_atacadao"
    )
    @patch(
        "coleta.management.commands.triangular_precos.buscar_carrefour"
    )
    def test_indisponivel_ou_ean_divergente_nao_cria_trio(
        self, carrefour, atacadao, savegnago
    ):
        savegnago.return_value = [oferta("Savegnago")]
        item_atacadao = oferta("Atacadão")
        item_atacadao["codigo_barras"] = "7891111111111"
        atacadao.return_value = [item_atacadao]
        carrefour.return_value = [oferta("Carrefour")]

        call_command("triangular_precos", gravar=True, stdout=StringIO())
        self.assertEqual(Produto.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)
        carrefour.assert_not_called()

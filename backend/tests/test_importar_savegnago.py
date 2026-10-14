from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from catalogo.models import Produto, Supermercado
from precos.models import OfertaFonte, Preco


class ImportarSavegnagoTests(TestCase):
    def setUp(self):
        self.supermercado = Supermercado.objects.create(
            nome="Savegnago",
            endereco="Rua de teste, 100",
            cidade="Ribeirão Preto",
            estado="SP",
            site_url="https://www.savegnago.com.br",
            ativo=True,
        )

        self.item = {
            "id_externo": "999",
            "sku": "12345",
            "vendedor_id": "1",
            "vendedor_nome": "SUPERMERCADO SAVEGNAGO",
            "nome": "Feijão de Teste 1kg",
            "marca": "Marca Teste",
            "codigo_barras": "7891234567895",
            "preco": 6.95,
            "disponivel": True,
            "url": "https://www.savegnago.com.br/feijao-teste/p",
        }

    @patch("coleta.management.commands.importar_savegnago.buscar_produtos")
    def test_simulacao_nao_grava_dados(self, mock_buscar):
        mock_buscar.return_value = [self.item]

        call_command(
            "importar_savegnago",
            termo="feijão",
            quantidade=1,
            cep="14010000",
        )

        self.assertEqual(Produto.objects.count(), 0)
        self.assertEqual(OfertaFonte.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)

    @patch("coleta.management.commands.importar_savegnago.buscar_produtos")
    def test_gravacao_cria_produto_oferta_e_preco(self, mock_buscar):
        mock_buscar.return_value = [self.item]

        call_command(
            "importar_savegnago",
            termo="feijão",
            quantidade=1,
            cep="14010000",
            gravar=True,
        )

        produto = Produto.objects.get(
            codigo_barras=self.item["codigo_barras"]
        )
        oferta = OfertaFonte.objects.get(
            produto=produto,
            supermercado=self.supermercado,
            ativo=True,
        )

        self.assertEqual(produto.nome, "Feijão de Teste 1kg")
        self.assertEqual(oferta.codigo_externo, "12345")
        self.assertEqual(oferta.precos.count(), 1)
        self.assertEqual(oferta.precos.get().valor, Decimal("6.95"))

    @patch("coleta.management.commands.importar_savegnago.buscar_produtos")
    def test_preco_igual_nao_duplica_historico(self, mock_buscar):
        produto = Produto.objects.create(
            nome="Feijão de Teste 1kg",
            marca="Marca Teste",
            codigo_barras=self.item["codigo_barras"],
        )
        oferta = OfertaFonte.objects.create(
            produto=produto,
            supermercado=self.supermercado,
            codigo_externo="12345",
            nome_externo=self.item["nome"],
            url_fonte=self.item["url"],
            ativo=True,
        )
        Preco.objects.create(
            oferta_fonte=oferta,
            valor=Decimal("6.95"),
            data_hora_coleta=__import__(
                "django.utils.timezone", fromlist=["now"]
            ).now(),
        )
        mock_buscar.return_value = [self.item]

        call_command(
            "importar_savegnago",
            termo="feijão",
            quantidade=1,
            cep="14010000",
            gravar=True,
        )

        self.assertEqual(oferta.precos.count(), 1)

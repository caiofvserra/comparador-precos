from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import requests
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from catalogo.models import Produto, Supermercado
from precos.models import OfertaFonte, Preco


EAN = "7891234567895"


class PopularComparacaoInicialTests(TestCase):
    def setUp(self):
        savegnago = Supermercado.objects.create(
            nome="Savegnago",
            endereco="",
            cidade="Ribeirão Preto",
            estado="SP",
            site_url="https://www.savegnago.com.br",
            ativo=True,
        )
        self.produto = Produto.objects.create(
            nome="Arroz Teste 1kg",
            marca="Marca Teste",
            codigo_barras=EAN,
        )
        oferta = OfertaFonte.objects.create(
            produto=self.produto,
            supermercado=savegnago,
            codigo_externo="1",
            nome_externo=self.produto.nome,
            url_fonte="https://www.savegnago.com.br/arroz-teste/p",
            ativo=True,
        )
        Preco.objects.create(
            oferta_fonte=oferta,
            valor=Decimal("7.00"),
            data_hora_coleta=timezone.now(),
        )

    def test_so_grava_preco_real_de_mesmo_ean_nas_outras_redes(self):
        def atacadao(termo, quantidade, cep):
            if termo != "arroz":
                return []
            return [{
                "id_externo": "123",
                "sku": "345",
                "vendedor_id": "1",
                "vendedor_nome": "ATACADAO",
                "nome": "Arroz Teste 1kg",
                "marca": "Marca Teste",
                "codigo_barras": EAN,
                "preco": "6.50",
                "disponivel": True,
                "url": "https://www.atacadao.com.br/arroz-teste/p",
            }]

        def carrefour(termo, quantidade):
            if termo != "arroz":
                return []
            return [{
                "nome": "Arroz Teste 1kg",
                "marca": "Marca Teste",
                "codigo_barras": EAN,
                "sku": "777",
                "preco": "6.70",
                "disponivel": True,
                "url": "https://mercado.carrefour.com.br/produto/arroz-teste",
            }]

        with (
            patch(
                "coleta.management.commands.importar_atacadao.buscar_produtos",
                side_effect=atacadao,
            ),
            patch(
                "coleta.management.commands.atualizar_precos_carrefour.buscar_produtos",
                side_effect=carrefour,
            ),
        ):
            call_command(
                "popular_comparacao_inicial", stdout=StringIO(), stderr=StringIO()
            )
            call_command(
                "popular_comparacao_inicial", stdout=StringIO(), stderr=StringIO()
            )

        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(Supermercado.objects.count(), 3)
        self.assertEqual(OfertaFonte.objects.count(), 3)
        self.assertEqual(Preco.objects.count(), 3)
        self.assertEqual(
            set(Preco.objects.values_list("valor", flat=True)),
            {Decimal("7.00"), Decimal("6.50"), Decimal("6.70")},
        )

    def test_fontes_indisponiveis_nao_inventam_precos(self):
        with (
            patch(
                "coleta.management.commands.importar_atacadao.buscar_produtos",
                side_effect=requests.RequestException("erro de rede"),
            ),
            patch(
                "coleta.management.commands.atualizar_precos_carrefour.buscar_produtos",
                side_effect=requests.RequestException("erro de rede"),
            ),
        ):
            call_command(
                "popular_comparacao_inicial", stdout=StringIO(), stderr=StringIO()
            )

        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(OfertaFonte.objects.count(), 1)
        self.assertEqual(Preco.objects.count(), 1)

    def test_carrefour_nao_aumenta_catalogo_com_produto_sem_comparacao(self):
        item_sem_correspondencia = {
            "nome": "Arroz de outra marca 5 kg",
            "marca": "Outra Marca",
            "codigo_barras": "7891234567008",
            "sku": "outro-123",
            "preco": "17.90",
            "disponivel": True,
            "url": "https://mercado.carrefour.com.br/produto/outro-arroz",
        }
        with (
            patch(
                "coleta.management.commands.importar_atacadao.buscar_produtos",
                return_value=[],
            ),
            patch(
                "coleta.management.commands.atualizar_precos_carrefour.buscar_produtos",
                return_value=[item_sem_correspondencia],
            ) as busca_carrefour,
        ):
            call_command(
                "popular_comparacao_inicial",
                stdout=StringIO(),
                stderr=StringIO(),
            )

        self.assertGreaterEqual(busca_carrefour.call_count, 6)
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(OfertaFonte.objects.count(), 1)
        self.assertEqual(Preco.objects.count(), 1)

    def test_nao_consulta_sem_produtos_savegnago(self):
        Produto.objects.all().delete()
        with patch(
            "coleta.management.commands.importar_atacadao.buscar_produtos"
        ) as fonte:
            call_command(
                "popular_comparacao_inicial", stdout=StringIO(), stderr=StringIO()
            )
        fonte.assert_not_called()

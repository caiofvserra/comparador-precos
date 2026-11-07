from decimal import Decimal
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from catalogo.models import Produto, Supermercado
from precos.models import OfertaFonte, Preco
from coleta.vtex_ean import buscar_ean


EAN = "7896200115346"


def item(loja, ean=EAN):
    dominios = {
        "Savegnago": "https://www.savegnago.com.br",
        "Atacadão": "https://www.atacadao.com.br",
        "Carrefour": "https://mercado.carrefour.com.br",
    }
    return {
        "nome": "Feijão Broto Legal 1kg",
        "marca": "Broto Legal",
        "codigo_barras": ean,
        "sku": "123",
        "vendedor_nome": {
            "Savegnago": "SAVEGNAGO",
            "Atacadão": "ATACADAO",
            "Carrefour": "",
        }[loja],
        "preco": {
            "Savegnago": "9.49",
            "Atacadão": "9.29",
            "Carrefour": "10.49",
        }[loja],
        "disponivel": True,
        "url": dominios[loja] + "/produto/feijao",
    }


class VtexEANTests(TestCase):
    def test_filtro_exato_ignora_ean_divergente(self):
        resposta = Mock()
        resposta.status_code = 200
        resposta.json.return_value = [
            {
                "productName": "Feijão outra marca",
                "link": "https://www.atacadao.com.br/produto/outro",
                "brand": "Outro",
                "items": [
                    {
                        "ean": "7891111111111",
                        "itemId": "sku-1",
                        "sellers": [
                            {
                                "sellerName": "ATACADAO",
                                "commertialOffer": {
                                    "IsAvailable": True,
                                    "AvailableQuantity": 3,
                                    "Price": 7.99,
                                },
                            },
                        ],
                    }
                ],
            }
        ]
        sessao = Mock()
        sessao.get.return_value = resposta
        self.assertIsNone(buscar_ean("Atacadão", EAN, sessao))
        self.assertEqual(sessao.get.call_count, 2)

    def test_busca_ean_exato_confere_estoque_e_rede(self):
        resposta = Mock()
        resposta.status_code = 200
        resposta.json.return_value = [{
            "productName": "Feijão Broto Legal",
            "brand": "Broto Legal",
            "link": "https://www.atacadao.com.br/feijao/p",
            "items": [
                {
                    "ean": EAN,
                    "itemId": "sku-1",
                    "sellers": [{
                        "sellerName": "ATACADAO",
                        "commertialOffer": {
                            "IsAvailable": True,
                            "AvailableQuantity": 4,
                            "Price": 9.29,
                        },
                    }],
                }
            ],
        }]
        sessao = Mock()
        sessao.get.return_value = resposta
        resultado = buscar_ean("Atacadão", EAN, sessao)
        self.assertEqual(resultado["codigo_barras"], EAN)
        self.assertEqual(resultado["preco"], 9.29)
        self.assertIn("alternateIds_Ean", str(sessao.get.call_args))

    def test_fallback_fulltext_nao_aceita_outro_ean(self):
        vazio = Mock()
        vazio.status_code = 200
        vazio.json.return_value = []
        sessao = Mock()
        sessao.get.return_value = vazio
        self.assertIsNone(buscar_ean("Savegnago", EAN, sessao))
        self.assertEqual(sessao.get.call_count, 2)


class ValidarTriosPorEANTests(TestCase):
    def setUp(self):
        self.produto = Produto.objects.create(
            nome="Feijão Broto Legal 1kg",
            marca="Broto Legal",
            codigo_barras=EAN,
        )
        for loja in ("Savegnago", "Carrefour"):
            supermercado = Supermercado.objects.create(
                nome=loja, endereco="", cidade="Ribeirão Preto",
                estado="SP",
                site_url={
                    "Savegnago": "https://www.savegnago.com.br",
                    "Carrefour": "https://mercado.carrefour.com.br",
                }[loja], ativo=True,
            )
            oferta = OfertaFonte.objects.create(
                produto=self.produto, supermercado=supermercado,
                codigo_externo="123", nome_externo=self.produto.nome,
                url_fonte=item(loja)["url"], ativo=True,
            )
            Preco.objects.create(
                oferta_fonte=oferta,
                valor=Decimal(item(loja)["preco"]),
                data_hora_coleta=timezone.now(),
            )

    @patch("coleta.management.commands.validar_trios_por_ean.sessao_atacadao")
    @patch("coleta.management.commands.validar_trios_por_ean.buscar_ean")
    def test_completa_trio_existente_somente_por_ean(
        self, busca, sessao
    ):
        busca.return_value = item("Atacadão")
        call_command(
            "validar_trios_por_ean", gravar=True, sem_seeds=True,
            max_eans=2, max_buscas_carrefour=0, stdout=StringIO()
        )
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(Supermercado.objects.count(), 3)
        self.assertEqual(OfertaFonte.objects.count(), 3)
        self.assertEqual(Preco.objects.count(), 3)
        call_command(
            "validar_trios_por_ean", gravar=True, sem_seeds=True,
            max_eans=2, max_buscas_carrefour=0, stdout=StringIO()
        )
        self.assertEqual(Preco.objects.count(), 3)
        self.assertEqual(busca.call_count, 1)

    @patch("coleta.management.commands.validar_trios_por_ean.sessao_atacadao")
    @patch("coleta.management.commands.validar_trios_por_ean.buscar_ean")
    def test_sem_atacadao_nao_cria_preco_falso(self, busca, sessao):
        busca.return_value = None
        call_command(
            "validar_trios_por_ean", gravar=True, sem_seeds=True,
            max_eans=2, max_buscas_carrefour=0, stdout=StringIO()
        )
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(OfertaFonte.objects.count(), 2)
        self.assertEqual(Preco.objects.count(), 2)

    @patch("coleta.management.commands.validar_trios_por_ean.sessao_atacadao")
    @patch("coleta.management.commands.validar_trios_por_ean.buscar_ean")
    def test_simulacao_nao_grava_trio(self, busca, sessao):
        busca.return_value = item("Atacadão")
        call_command(
            "validar_trios_por_ean", sem_seeds=True,
            max_eans=2, max_buscas_carrefour=0, stdout=StringIO()
        )
        self.assertEqual(Preco.objects.count(), 2)

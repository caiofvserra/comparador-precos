from decimal import Decimal
from unittest.mock import Mock, call, patch

import requests
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from catalogo.models import Produto, Supermercado
from coleta.carrefour import _extrair_produto
from coleta.management.commands.atualizar_precos_todos import Command as AtualizarTodosCommand
from precos.models import OfertaFonte, Preco


class ColetaIntegracaoTests(TestCase):
    def test_simulacao_savegnago_nao_cria_supermercado(self):
        with patch(
            "coleta.management.commands.importar_savegnago.buscar_produtos",
            return_value=[],
        ):
            call_command(
                "importar_savegnago",
                termo="arroz",
                quantidade=1,
                cep="14010000",
            )

        self.assertFalse(
            Supermercado.objects.filter(nome__iexact="Savegnago").exists()
        )

    def test_savegnago_preenche_imagem_de_produto_existente(self):
        supermercado = Supermercado.objects.create(
            nome="Savegnago",
            endereco="",
            cidade="Ribeirão Preto",
            estado="SP",
            site_url="https://www.savegnago.com.br",
            ativo=True,
        )
        produto = Produto.objects.create(
            nome="Feijão teste",
            marca="Marca teste",
            codigo_barras="7891234567895",
        )
        oferta = OfertaFonte.objects.create(
            produto=produto,
            supermercado=supermercado,
            codigo_externo="12345",
            nome_externo="Feijão teste",
            url_fonte="https://www.savegnago.com.br/feijao-teste/p",
            ativo=True,
        )
        Preco.objects.create(
            oferta_fonte=oferta,
            valor=Decimal("6.95"),
            data_hora_coleta=timezone.now(),
        )

        item = {
            "id_externo": "999",
            "sku": "12345",
            "vendedor_id": "1",
            "vendedor_nome": "SUPERMERCADO SAVEGNAGO",
            "nome": "Feijão teste",
            "marca": "Marca teste",
            "codigo_barras": "7891234567895",
            "preco": 6.95,
            "disponivel": True,
            "url": "https://www.savegnago.com.br/feijao-teste/p",
            "imagem_url": "https://www.savegnago.com.br/imagem/feijao.jpg",
        }

        with patch(
            "coleta.management.commands.importar_savegnago.buscar_produtos",
            return_value=[item],
        ):
            call_command(
                "importar_savegnago",
                termo="feijão",
                quantidade=1,
                cep="14010000",
                gravar=True,
            )

        produto.refresh_from_db()
        self.assertEqual(
            produto.imagem_url,
            "https://www.savegnago.com.br/imagem/feijao.jpg",
        )
        self.assertEqual(oferta.precos.count(), 1)

    def test_atacadao_importa_imagem(self):
        item = {
            "id_externo": "999",
            "sku": "54321",
            "vendedor_id": "1",
            "vendedor_nome": "ATACADAO",
            "nome": "Arroz teste",
            "marca": "Marca teste",
            "codigo_barras": "7891234567895",
            "preco": 22.90,
            "disponivel": True,
            "url": "https://www.atacadao.com.br/arroz-teste/p",
            "imagem_url": "https://www.atacadao.com.br/imagem/arroz.jpg",
        }

        with patch(
            "coleta.management.commands.importar_atacadao.buscar_produtos",
            return_value=[item],
        ):
            call_command(
                "importar_atacadao",
                termo="arroz",
                quantidade=1,
                cep="14010000",
                gravar=True,
            )

        produto = Produto.objects.get(codigo_barras="7891234567895")
        self.assertEqual(
            produto.imagem_url,
            "https://www.atacadao.com.br/imagem/arroz.jpg",
        )

    def test_carrefour_extrai_imagem_do_json_ld(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "Café Teste",
          "brand": {"@type": "Brand", "name": "Marca Teste"},
          "gtin13": "7891234567895",
          "sku": "ABC123",
          "image": ["https://mercado.carrefour.com.br/imagem/cafe.jpg"],
          "offers": {
            "@type": "Offer",
            "price": "19.90",
            "availability": "https://schema.org/InStock"
          }
        }
        </script>
        </head></html>
        """

        produto = _extrair_produto(
            html,
            "https://mercado.carrefour.com.br/produto/cafe-teste",
        )

        self.assertIsNotNone(produto)
        self.assertEqual(
            produto["imagem_url"],
            "https://mercado.carrefour.com.br/imagem/cafe.jpg",
        )

    def test_carrefour_cria_supermercado_e_salva_imagem(self):
        produto = Produto.objects.create(
            nome="Café teste",
            marca="Marca teste",
            codigo_barras="7891234567895",
        )
        item = {
            "nome": "Café teste",
            "marca": "Marca teste",
            "codigo_barras": "7891234567895",
            "sku": "ABC123",
            "preco": 19.90,
            "disponivel": True,
            "url": "https://mercado.carrefour.com.br/produto/cafe-teste",
            "imagem_url": "https://mercado.carrefour.com.br/imagem/cafe.jpg",
        }

        with patch(
            "coleta.management.commands.atualizar_precos_carrefour.buscar_produtos",
            return_value=[item],
        ):
            call_command(
                "atualizar_precos_carrefour",
                termo="café",
                quantidade=1,
                gravar=True,
            )

        produto.refresh_from_db()
        supermercado = Supermercado.objects.get(nome="Carrefour")
        oferta = OfertaFonte.objects.get(
            produto=produto,
            supermercado=supermercado,
            ativo=True,
        )
        self.assertEqual(
            produto.imagem_url,
            "https://mercado.carrefour.com.br/imagem/cafe.jpg",
        )
        self.assertEqual(oferta.precos.count(), 1)

    def test_simulacao_carrefour_nao_cria_supermercado(self):
        Produto.objects.create(
            nome="Café teste",
            marca="Marca teste",
            codigo_barras="7891234567895",
        )
        item = {
            "nome": "Café teste",
            "marca": "Marca teste",
            "codigo_barras": "7891234567895",
            "sku": "ABC123",
            "preco": 19.90,
            "disponivel": True,
            "url": "https://mercado.carrefour.com.br/produto/cafe-teste",
            "imagem_url": "",
        }

        with patch(
            "coleta.management.commands.atualizar_precos_carrefour.buscar_produtos",
            return_value=[item],
        ):
            call_command(
                "atualizar_precos_carrefour",
                termo="café",
                quantidade=1,
            )

        self.assertFalse(
            Supermercado.objects.filter(nome__iexact="Carrefour").exists()
        )
        self.assertEqual(OfertaFonte.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)


class AtualizacaoPrecosTests(TestCase):
    def criar_oferta(self, nome_supermercado, site_url, sku="12345"):
        supermercado = Supermercado.objects.create(
            nome=nome_supermercado,
            endereco="",
            cidade="Ribeirão Preto",
            estado="SP",
            site_url=site_url,
            ativo=True,
        )
        produto = Produto.objects.create(
            nome="Produto teste",
            marca="Marca teste",
            codigo_barras="7891234567895",
        )
        oferta = OfertaFonte.objects.create(
            produto=produto,
            supermercado=supermercado,
            codigo_externo=sku,
            nome_externo="Produto teste",
            url_fonte=f"{site_url}/produto-teste",
            ativo=True,
        )
        Preco.objects.create(
            oferta_fonte=oferta,
            valor=Decimal("10.00"),
            data_hora_coleta=timezone.now(),
        )
        return produto, oferta

    def test_ct08_falha_de_coleta_preserva_ultimo_preco(self):
        _, oferta = self.criar_oferta(
            "Savegnago",
            "https://www.savegnago.com.br",
        )

        with patch(
            "coleta.management.commands.atualizar_precos_savegnago.criar_sessao",
            side_effect=requests.RequestException("falha simulada"),
        ):
            call_command(
                "atualizar_precos_savegnago",
                cep="14010000",
                gravar=True,
            )

        self.assertEqual(oferta.precos.count(), 1)
        self.assertEqual(oferta.precos.get().valor, Decimal("10.00"))

    def test_atacadao_atualiza_preco_e_imagem(self):
        produto, oferta = self.criar_oferta(
            "Atacadão",
            "https://www.atacadao.com.br",
        )
        resposta = Mock()
        resposta.raise_for_status.return_value = None
        resposta.json.return_value = [
            {
                "items": [
                    {
                        "itemId": "12345",
                        "ean": "7891234567895",
                        "images": [
                            {
                                "imageUrl":
                                    "https://www.atacadao.com.br/imagem/produto.jpg"
                            }
                        ],
                        "sellers": [
                            {
                                "sellerName": "ATACADAO",
                                "commertialOffer": {
                                    "IsAvailable": True,
                                    "AvailableQuantity": 10,
                                    "Price": 11.50,
                                },
                            }
                        ],
                    }
                ]
            }
        ]
        sessao = Mock()
        sessao.get.return_value = resposta

        with patch(
            "coleta.management.commands.atualizar_precos_atacadao.criar_sessao",
            return_value=sessao,
        ):
            call_command(
                "atualizar_precos_atacadao",
                cep="14010000",
                gravar=True,
            )

        produto.refresh_from_db()
        self.assertEqual(oferta.precos.count(), 2)
        self.assertEqual(
            oferta.precos.order_by("-data_hora_coleta").first().valor,
            Decimal("11.50"),
        )
        self.assertEqual(
            produto.imagem_url,
            "https://www.atacadao.com.br/imagem/produto.jpg",
        )

    def test_carrefour_preco_igual_nao_duplica_historico(self):
        produto, oferta = self.criar_oferta(
            "Carrefour",
            "https://mercado.carrefour.com.br",
            sku="ABC123",
        )
        item = {
            "nome": "Produto teste",
            "marca": "Marca teste",
            "codigo_barras": produto.codigo_barras,
            "sku": "ABC123",
            "preco": 10.00,
            "disponivel": True,
            "url": "https://mercado.carrefour.com.br/produto/produto-teste",
            "imagem_url": "",
        }

        with patch(
            "coleta.management.commands.atualizar_precos_carrefour.buscar_produtos",
            return_value=[item],
        ):
            call_command(
                "atualizar_precos_carrefour",
                todos=True,
                gravar=True,
            )

        self.assertEqual(oferta.precos.count(), 1)


class AtualizarTodosTests(TestCase):
    @patch("coleta.management.commands.atualizar_precos_todos.call_command")
    def test_comando_chama_as_tres_redes(self, mock_call_command):
        AtualizarTodosCommand().handle(cep="14010000", gravar=True)

        self.assertEqual(
            mock_call_command.call_args_list,
            [
                call(
                    "atualizar_precos_savegnago",
                    gravar=True,
                    cep="14010000",
                ),
                call(
                    "atualizar_precos_atacadao",
                    gravar=True,
                    cep="14010000",
                ),
                call(
                    "atualizar_precos_carrefour",
                    gravar=True,
                    todos=True,
                ),
            ],
        )

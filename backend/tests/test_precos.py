from datetime import datetime, timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APITestCase

from catalogo.models import Produto, Supermercado
from precos.models import OfertaFonte, Preco


class RegrasDePrecoTests(TestCase):
    fixtures = ["dados_exemplo"]

    def setUp(self):
        # oferta do Arroz (101) no Mercado A, que já tem 2 preços na fixture
        self.oferta = OfertaFonte.objects.get(produto=101, supermercado=1)

    def test_ct07_nova_coleta_nao_apaga_historico(self):
        antes = self.oferta.precos.count()

        Preco.objects.create(
            oferta_fonte=self.oferta,
            valor=Decimal("25.50"),
            data_hora_coleta=datetime(2026, 9, 23, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(self.oferta.precos.count(), antes + 1)
        self.assertEqual(self.oferta.precos.first().valor, Decimal("25.50"))

    def test_rn09_preco_zero_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            Preco.objects.create(
                oferta_fonte=self.oferta,
                valor=Decimal("0.00"),
                data_hora_coleta=datetime(2026, 9, 23, 8, 0, tzinfo=timezone.utc),
            )

    def test_rn09_preco_negativo_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            Preco.objects.create(
                oferta_fonte=self.oferta,
                valor=Decimal("-1.00"),
                data_hora_coleta=datetime(2026, 9, 23, 8, 0, tzinfo=timezone.utc),
            )

    def test_rn10_segunda_oferta_ativa_no_mesmo_mercado_e_rejeitada(self):
        with self.assertRaises(ValidationError):
            OfertaFonte.objects.create(
                produto=Produto.objects.get(pk=101),
                supermercado=Supermercado.objects.get(pk=1),
                nome_externo="Arroz A 5kg (duplicado)",
                url_fonte="https://www.mercadoa.com.br/produto/dup",
                ativo=True,
            )

    def test_rn10_segunda_oferta_inativa_e_permitida(self):
        oferta = OfertaFonte.objects.create(
            produto=Produto.objects.get(pk=101),
            supermercado=Supermercado.objects.get(pk=1),
            nome_externo="Arroz A 5kg (antigo)",
            url_fonte="https://www.mercadoa.com.br/produto/antigo",
            ativo=False,
        )

        self.assertIsNotNone(oferta.pk)

    def test_oferta_sem_produto_da_erro_de_validacao(self):
        oferta = OfertaFonte(nome_externo="Sem produto", url_fonte="https://www.mercadoa.com.br/x")

        with self.assertRaises(ValidationError):
            oferta.full_clean()

    def test_rn10_editar_a_propria_oferta_ativa_nao_conflita(self):
        self.oferta.nome_externo = "Arroz Marca A 5kg - novo nome"
        self.oferta.save()  # não deve levantar erro


class CorsTests(APITestCase):
    fixtures = ["dados_exemplo"]

    def test_origem_do_front_recebe_cabecalho_cors(self):
        resposta = self.client.get(
            "/api/v1/supermercados/", HTTP_ORIGIN="http://localhost:5173"
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Access-Control-Allow-Origin"], "http://localhost:5173")

    def test_origem_desconhecida_nao_recebe_cabecalho_cors(self):
        resposta = self.client.get(
            "/api/v1/supermercados/", HTTP_ORIGIN="http://site-desconhecido.com"
        )

        self.assertNotIn("Access-Control-Allow-Origin", resposta)

from rest_framework.test import APITestCase


class ComparacaoTests(APITestCase):
    fixtures = ["dados_exemplo"]

    def test_ct03_produto_com_preco_em_tres_mercados(self):
        resposta = self.client.get("/api/v1/produtos/101/comparacao/")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["produto"], {
            "id": 101, "nome": "Arroz 5 kg", "marca": "Marca A", "codigo_barras": "7890000000101",
        })

        precos = resposta.data["precos"]
        self.assertEqual(len(precos), 3)
        for item in precos:
            self.assertTrue(item["disponivel"])
            self.assertIsNotNone(item["data_hora_coleta"])
            self.assertTrue(item["url_fonte"].startswith("https://"))

    def test_preco_retornado_e_o_mais_recente(self):
        resposta = self.client.get("/api/v1/produtos/101/comparacao/")

        por_mercado = {p["supermercado"]["nome"]: p for p in resposta.data["precos"]}
        # Mercado C tem 24.00, 23.90 e 23.50; vale o último coletado
        self.assertEqual(por_mercado["Mercado C"]["valor"], "23.50")
        self.assertEqual(por_mercado["Mercado A"]["valor"], "24.90")

    def test_valor_e_string_decimal_e_data_iso_com_fuso(self):
        resposta = self.client.get("/api/v1/produtos/101/comparacao/")

        item = resposta.data["precos"][0]
        self.assertIsInstance(item["valor"], str)
        self.assertEqual(item["data_hora_coleta"], "2026-09-22T18:20:00-03:00")

    def test_ct04_mercado_sem_preco_e_indicado_sem_inventar_valor(self):
        # Café (103) só tem oferta nos mercados A e B
        resposta = self.client.get("/api/v1/produtos/103/comparacao/")

        self.assertEqual(resposta.status_code, 200)
        por_mercado = {p["supermercado"]["nome"]: p for p in resposta.data["precos"]}
        self.assertEqual(len(por_mercado), 3)

        ausente = por_mercado["Mercado C"]
        self.assertFalse(ausente["disponivel"])
        self.assertIsNone(ausente["valor"])
        self.assertIsNone(ausente["data_hora_coleta"])
        self.assertIsNone(ausente["url_fonte"])

        self.assertTrue(por_mercado["Mercado A"]["disponivel"])
        self.assertEqual(por_mercado["Mercado A"]["valor"], "19.90")

    def test_oferta_sem_nenhum_preco_conta_como_indisponivel(self):
        from precos.models import Preco

        Preco.objects.filter(oferta_fonte__produto=103, oferta_fonte__supermercado=2).delete()

        resposta = self.client.get("/api/v1/produtos/103/comparacao/")

        por_mercado = {p["supermercado"]["nome"]: p for p in resposta.data["precos"]}
        self.assertFalse(por_mercado["Mercado B"]["disponivel"])

    def test_produto_inexistente_retorna_404(self):
        resposta = self.client.get("/api/v1/produtos/9999/comparacao/")

        self.assertEqual(resposta.status_code, 404)

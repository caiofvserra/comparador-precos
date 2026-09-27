from rest_framework.test import APITestCase


class HistoricoTests(APITestCase):
    fixtures = ["dados_exemplo"]

    def test_historico_de_todos_os_mercados_ordenado_por_data(self):
        resposta = self.client.get("/api/v1/produtos/101/historico/")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["produto"]["id"], 101)

        historico = resposta.data["historico"]
        # 2 preços no A + 2 no B + 3 no C
        self.assertEqual(len(historico), 7)
        datas = [h["data_hora_coleta"] for h in historico]
        self.assertEqual(datas, sorted(datas))

    def test_cada_registro_tem_supermercado_valor_data_e_fonte(self):
        resposta = self.client.get("/api/v1/produtos/101/historico/")

        registro = resposta.data["historico"][0]
        self.assertEqual(set(registro.keys()), {"supermercado", "valor", "data_hora_coleta", "url_fonte"})
        self.assertEqual(registro["supermercado"], {"id": 3, "nome": "Mercado C"})
        self.assertEqual(registro["valor"], "24.00")

    def test_filtro_por_supermercado(self):
        resposta = self.client.get("/api/v1/produtos/101/historico/", {"supermercado_id": 3})

        historico = resposta.data["historico"]
        self.assertEqual([h["valor"] for h in historico], ["24.00", "23.90", "23.50"])
        for h in historico:
            self.assertEqual(h["supermercado"]["id"], 3)

    def test_supermercado_sem_dados_retorna_lista_vazia(self):
        # Café (103) não tem oferta no Mercado C
        resposta = self.client.get("/api/v1/produtos/103/historico/", {"supermercado_id": 3})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["historico"], [])

    def test_supermercado_id_vazio_retorna_historico_completo(self):
        resposta = self.client.get("/api/v1/produtos/101/historico/", {"supermercado_id": ""})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data["historico"]), 7)

    def test_supermercado_id_invalido_retorna_400(self):
        resposta = self.client.get("/api/v1/produtos/101/historico/", {"supermercado_id": "abc"})

        self.assertEqual(resposta.status_code, 400)

    def test_produto_inexistente_retorna_404(self):
        resposta = self.client.get("/api/v1/produtos/9999/historico/")

        self.assertEqual(resposta.status_code, 404)

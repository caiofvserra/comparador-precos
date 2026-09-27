from rest_framework.test import APITestCase
from catalogo.models import Produto

class ProdutoBuscaTests(APITestCase):
    fixtures = ["dados_exemplo"]

    def test_ct01_busca_produto_existente(self):
        resposta = self.client.get("/api/v1/produtos/", {"q": "arroz"})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data), 1)
        self.assertEqual(resposta.data[0]["id"], 101)
        self.assertEqual(resposta.data[0]["nome"], "Arroz 5 kg")
        self.assertEqual(resposta.data[0]["marca"], "Marca A")

    def test_busca_por_marca(self):
        resposta = self.client.get("/api/v1/produtos/", {"q": "marca f"})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([p["id"] for p in resposta.data], [205])

    def test_ct02_busca_termo_inexistente_retorna_vazio(self):
        resposta = self.client.get("/api/v1/produtos/", {"q": "xyz-nao-existe"})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data, [])

    def test_sem_q_retorna_todos_ordenados_por_nome(self):
        resposta = self.client.get("/api/v1/produtos/")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data), 6)
        # compara com a ordem do próprio banco (a regra de acentos depende da instalação)
        esperado = list(Produto.objects.order_by("nome").values_list("nome", flat=True))
        self.assertEqual([p["nome"] for p in resposta.data], esperado)


class SupermercadoListaTests(APITestCase):
    fixtures = ["dados_exemplo"]

    def test_lista_supermercados_ativos(self):
        resposta = self.client.get("/api/v1/supermercados/")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([s["nome"] for s in resposta.data], ["Mercado A", "Mercado B", "Mercado C"])
        self.assertIn("site_url", resposta.data[0])

    def test_supermercado_inativo_nao_aparece(self):
        from catalogo.models import Supermercado

        Supermercado.objects.filter(pk=3).update(ativo=False)

        resposta = self.client.get("/api/v1/supermercados/")

        self.assertEqual([s["id"] for s in resposta.data], [1, 2])

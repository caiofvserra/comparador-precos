from rest_framework.test import APITestCase

from catalogo.models import Produto


class ProdutoBuscaTests(APITestCase):
    fixtures = ["dados_exemplo"]

    def test_ct01_busca_produto_existente(self):
        resposta = self.client.get(
            "/api/v1/produtos/",
            {"q": "arroz"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data), 1)

        produto = resposta.data[0]

        self.assertEqual(produto["id"], 101)
        self.assertEqual(produto["nome"], "Arroz 5 kg")
        self.assertEqual(produto["marca"], "Marca A")

    def test_busca_por_marca(self):
        resposta = self.client.get(
            "/api/v1/produtos/",
            {"q": "marca f"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            [p["id"] for p in resposta.data],
            [205],
        )

    def test_ct02_busca_termo_inexistente_retorna_vazio(self):
        resposta = self.client.get(
            "/api/v1/produtos/",
            {"q": "xyz-nao-existe"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data, [])

    def test_sem_q_retorna_todos_ordenados_por_nome(self):
        resposta = self.client.get(
            "/api/v1/produtos/"
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data), 6)

        esperado = list(
            Produto.objects
            .order_by("nome")
            .values_list("nome", flat=True)
        )

        self.assertEqual(
            [p["nome"] for p in resposta.data],
            esperado,
        )

    def test_produto_retorna_dados_usados_pelo_front(self):
        resposta = self.client.get(
            "/api/v1/produtos/",
            {"q": "arroz"},
        )

        produto = resposta.data[0]

        self.assertIn("imagem_url", produto)
        self.assertIn("categorias", produto)
        self.assertIn("preco_minimo", produto)
        self.assertIn("preco_maximo", produto)

        self.assertIsNone(produto["imagem_url"])
        self.assertEqual(
            produto["categorias"],
            ["Grãos"],
        )
        self.assertEqual(
            produto["preco_minimo"],
            "23.50",
        )
        self.assertEqual(
            produto["preco_maximo"],
            "24.90",
        )


    def test_filtra_apenas_produtos_com_precos_em_tres_redes(self):
        from django.utils import timezone
        from catalogo.models import Supermercado
        from precos.models import OfertaFonte, Preco

        produto = Produto.objects.create(
            nome="Biscoito experimental comparável",
            marca="Marca experimental",
            codigo_barras="7891234567001",
        )
        mercados = list(Supermercado.objects.filter(ativo=True)[:3])
        self.assertEqual(len(mercados), 3)
        for indice, supermercado in enumerate(mercados):
            oferta = OfertaFonte.objects.create(
                produto=produto,
                supermercado=supermercado,
                codigo_externo=str(indice),
                nome_externo=produto.nome,
                url_fonte="https://example.com/produto",
                ativo=True,
            )
            Preco.objects.create(
                oferta_fonte=oferta,
                valor=10 + indice,
                data_hora_coleta=timezone.now(),
            )

        resposta = self.client.get(
            "/api/v1/produtos/",
            {"q": "Biscoito experimental", "min_redes": "3"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data), 1)
        self.assertEqual(resposta.data[0]["id"], produto.id)
        self.assertEqual(resposta.data[0]["quantidade_redes"], 3)

    def test_filtro_com_numero_de_redes_invalido_retorna_400(self):
        resposta = self.client.get(
            "/api/v1/produtos/", {"min_redes": "4"}
        )
        self.assertEqual(resposta.status_code, 400)

    def test_priorizacao_por_redes_sem_alterar_ordem_padrao(self):
        from django.utils import timezone
        from catalogo.models import Supermercado
        from precos.models import OfertaFonte, Preco

        isolado = Produto.objects.create(
            nome="A Experimental isolado",
            codigo_barras="7891234567002",
        )
        comparavel = Produto.objects.create(
            nome="Z Experimental completo",
            codigo_barras="7891234567003",
        )
        mercados = list(Supermercado.objects.filter(ativo=True)[:3])
        for indice, supermercado in enumerate(mercados):
            for produto in ([isolado, comparavel] if indice == 0 else [comparavel]):
                oferta = OfertaFonte.objects.create(
                    produto=produto, supermercado=supermercado,
                    codigo_externo=str(indice),
                    nome_externo=produto.nome,
                    url_fonte="https://example.com/preco",
                    ativo=True,
                )
                Preco.objects.create(
                    oferta_fonte=oferta, valor=10 + indice,
                    data_hora_coleta=timezone.now(),
                )

        normal = self.client.get(
            "/api/v1/produtos/", {"q": "Experimental"}
        )
        priorizado = self.client.get(
            "/api/v1/produtos/",
            {"q": "Experimental", "priorizar_redes": "1"},
        )
        self.assertEqual(
            [produto["id"] for produto in normal.data],
            [isolado.id, comparavel.id],
        )
        self.assertEqual(
            [produto["id"] for produto in priorizado.data],
            [comparavel.id, isolado.id],
        )


class SupermercadoListaTests(APITestCase):
    fixtures = ["dados_exemplo"]

    def test_lista_supermercados_ativos(self):
        resposta = self.client.get(
            "/api/v1/supermercados/"
        )

        self.assertEqual(resposta.status_code, 200)

        self.assertEqual(
            [s["nome"] for s in resposta.data],
            [
                "Mercado A",
                "Mercado B",
                "Mercado C",
            ],
        )

        self.assertIn(
            "site_url",
            resposta.data[0],
        )

    def test_supermercado_inativo_nao_aparece(self):
        from catalogo.models import Supermercado

        Supermercado.objects.filter(
            pk=3
        ).update(ativo=False)

        resposta = self.client.get(
            "/api/v1/supermercados/"
        )

        self.assertEqual(
            [s["id"] for s in resposta.data],
            [1, 2],
        )
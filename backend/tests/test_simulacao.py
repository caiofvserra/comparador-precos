from decimal import Decimal

from rest_framework.test import APITestCase


class SimulacaoListaTests(APITestCase):
    fixtures = ["dados_exemplo"]

    def simular(self, itens):
        return self.client.post("/api/v1/listas/simular/", {"itens": itens}, format="json")

    def test_exemplo_do_contrato(self):
        # Mesmo exemplo da seção 11.2 da especificação
        resposta = self.simular([
            {"produto_id": 101, "quantidade": 2},
            {"produto_id": 205, "quantidade": 1},
        ])

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["total_itens"], 2)

        por_mercado = {s["supermercado"]["nome"]: s for s in resposta.data["supermercados"]}
        self.assertEqual(por_mercado["Mercado A"], {
            "supermercado": {"id": 1, "nome": "Mercado A"},
            "status": "completo",
            "itens_encontrados": 2,
            "total": "67.70",
            "itens": [
                {"produto_id": 101, "quantidade": 2, "valor_unitario": "24.90", "subtotal": "49.80"},
                {"produto_id": 205, "quantidade": 1, "valor_unitario": "17.90", "subtotal": "17.90"},
            ],
            "itens_ausentes": [],
        })
        self.assertEqual(por_mercado["Mercado B"], {
            "supermercado": {"id": 2, "nome": "Mercado B"},
            "status": "incompleto",
            "itens_encontrados": 1,
            "total": "49.80",
            "itens": [
                {"produto_id": 101, "quantidade": 2, "valor_unitario": "24.90", "subtotal": "49.80"},
            ],
            "itens_ausentes": [205],
        })

    def test_ct05_lista_com_todos_os_itens_disponiveis(self):
        resposta = self.simular([
            {"produto_id": 101, "quantidade": 1},
            {"produto_id": 102, "quantidade": 3},
            {"produto_id": 105, "quantidade": 2},
        ])

        por_mercado = {s["supermercado"]["nome"]: s for s in resposta.data["supermercados"]}
        for nome in ["Mercado A", "Mercado B", "Mercado C"]:
            self.assertEqual(por_mercado[nome]["status"], "completo")
            self.assertEqual(por_mercado[nome]["itens_encontrados"], 3)
        # A: 24.90 + 3*8.99 + 2*2.49 = 24.90 + 26.97 + 4.98
        self.assertEqual(por_mercado["Mercado A"]["total"], "56.85")
        # C: 23.50 + 3*8.60 + 2*2.59 = 23.50 + 25.80 + 5.18
        self.assertEqual(por_mercado["Mercado C"]["total"], "54.48")
        self.assertEqual(
            [i["subtotal"] for i in por_mercado["Mercado C"]["itens"]],
            ["23.50", "25.80", "5.18"],
        )

        # soma dos subtotais bate com o total em todos os mercados
        for resultado in resposta.data["supermercados"]:
            soma = sum(Decimal(i["subtotal"]) for i in resultado["itens"])
            self.assertEqual(soma, Decimal(resultado["total"]))

    def test_ct06_item_ausente_marca_incompleto_e_lista_o_item(self):
        # Café (103) não existe no Mercado C; Leite (104) não existe no B
        resposta = self.simular([
            {"produto_id": 103, "quantidade": 1},
            {"produto_id": 104, "quantidade": 2},
        ])

        por_mercado = {s["supermercado"]["nome"]: s for s in resposta.data["supermercados"]}
        self.assertEqual(por_mercado["Mercado A"]["status"], "completo")
        self.assertEqual(por_mercado["Mercado A"]["total"], "29.88")

        self.assertEqual(por_mercado["Mercado B"]["status"], "incompleto")
        self.assertEqual(por_mercado["Mercado B"]["itens_ausentes"], [104])
        self.assertEqual(por_mercado["Mercado B"]["total"], "18.50")

        self.assertEqual(por_mercado["Mercado C"]["status"], "incompleto")
        self.assertEqual(por_mercado["Mercado C"]["itens_ausentes"], [103])
        self.assertEqual(por_mercado["Mercado C"]["itens_encontrados"], 1)

    def test_total_e_string_decimal_com_duas_casas(self):
        resposta = self.simular([{"produto_id": 105, "quantidade": 1}])

        total = resposta.data["supermercados"][0]["total"]
        self.assertIsInstance(total, str)
        self.assertEqual(total, "2.49")

    def test_lista_vazia_retorna_400(self):
        resposta = self.simular([])

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("itens", resposta.data)

    def test_sem_campo_itens_retorna_400(self):
        resposta = self.client.post("/api/v1/listas/simular/", {}, format="json")

        self.assertEqual(resposta.status_code, 400)

    def test_quantidade_zero_retorna_400(self):
        resposta = self.simular([{"produto_id": 101, "quantidade": 0}])

        self.assertEqual(resposta.status_code, 400)

    def test_quantidade_acima_do_limite_retorna_400(self):
        resposta = self.simular([{"produto_id": 101, "quantidade": 1001}])

        self.assertEqual(resposta.status_code, 400)

    def test_produto_inexistente_retorna_400(self):
        resposta = self.simular([{"produto_id": 9999, "quantidade": 1}])

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("produto_id", resposta.data["itens"][0])

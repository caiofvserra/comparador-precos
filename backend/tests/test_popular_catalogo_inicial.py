from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from catalogo.models import Produto
from precos.models import Preco


class PopularCatalogoInicialTests(TestCase):
    def test_importa_ofertas_reais_e_para_ao_atingir_limite(self):
        def dados_do_termo(termo, quantidade, cep):
            return [
                {
                    "id_externo": f"{termo}-{i}",
                    "sku": f"{termo}-{i}",
                    "vendedor_id": "1",
                    "vendedor_nome": "SUPERMERCADO SAVEGNAGO",
                    "nome": f"Produto {termo} {i}",
                    "marca": "Marca Teste",
                    "codigo_barras": str(7891234567000 + i + (0 if termo == "arroz" else 100)),
                    "preco": "5.95",
                    "disponivel": True,
                    "url": f"https://www.savegnago.com.br/{termo}-{i}/p",
                    "imagem_url": "https://www.savegnago.com.br/foto.png",
                }
                for i in range(quantidade)
            ]

        with patch(
            "coleta.management.commands.importar_savegnago.buscar_produtos",
            side_effect=dados_do_termo,
        ) as buscar:
            call_command(
                "popular_catalogo_inicial",
                stdout=StringIO(),
                stderr=StringIO(),
            )

        self.assertEqual(buscar.call_count, 2)
        self.assertEqual(Produto.objects.count(), 24)
        self.assertEqual(Preco.objects.count(), 24)

    def test_catalogo_com_ofertas_suficientes_nao_coleta_novamente(self):
        def dados_do_termo(termo, quantidade, cep):
            return [
                {
                    "id_externo": f"{termo}-{i}",
                    "sku": f"{termo}-{i}",
                    "vendedor_id": "1",
                    "vendedor_nome": "SUPERMERCADO SAVEGNAGO",
                    "nome": f"Produto {termo} {i}",
                    "marca": "Marca Teste",
                    "codigo_barras": str(7891234567000 + i + (0 if termo == "arroz" else 100)),
                    "preco": "5.95",
                    "disponivel": True,
                    "url": f"https://www.savegnago.com.br/{termo}-{i}/p",
                }
                for i in range(quantidade)
            ]

        with patch(
            "coleta.management.commands.importar_savegnago.buscar_produtos",
            side_effect=dados_do_termo,
        ) as buscar:
            call_command("popular_catalogo_inicial", stdout=StringIO(), stderr=StringIO())
            call_command("popular_catalogo_inicial", stdout=StringIO(), stderr=StringIO())

        self.assertEqual(buscar.call_count, 2)
        self.assertEqual(Produto.objects.count(), 24)
        self.assertEqual(Preco.objects.count(), 24)

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from catalogo.models import Produto
from coleta.management.commands.popular_catalogo_inicial import TERMOS_INICIAIS
from precos.models import Preco


def dados_do_termo(termo, quantidade, cep):
    indice = TERMOS_INICIAIS.index(termo)
    return [
        {
            "id_externo": f"{termo}-{i}",
            "sku": f"{termo}-{i}",
            "vendedor_id": "1",
            "vendedor_nome": "SUPERMERCADO SAVEGNAGO",
            "nome": f"Produto {termo} {i}",
            "marca": "Marca Teste",
            "codigo_barras": str(7891234567000 + indice * 100 + i),
            "preco": "5.95",
            "disponivel": True,
            "url": f"https://www.savegnago.com.br/{termo}-{i}/p",
            "imagem_url": "https://www.savegnago.com.br/foto.png",
        }
        for i in range(quantidade)
    ]


class PopularCatalogoInicialTests(TestCase):
    @patch(
        "coleta.management.commands.importar_savegnago.buscar_produtos",
        side_effect=dados_do_termo,
    )
    def test_importa_ofertas_reais_em_todas_categorias(self, buscar):
        call_command(
            "popular_catalogo_inicial", stdout=StringIO(), stderr=StringIO()
        )

        self.assertEqual(buscar.call_count, len(TERMOS_INICIAIS))
        self.assertEqual(Produto.objects.count(), 12 * len(TERMOS_INICIAIS))
        self.assertEqual(Preco.objects.count(), 12 * len(TERMOS_INICIAIS))

    @patch(
        "coleta.management.commands.importar_savegnago.buscar_produtos",
        side_effect=dados_do_termo,
    )
    def test_segunda_execucao_nao_consulta_categoria_ja_preenchida(self, buscar):
        call_command(
            "popular_catalogo_inicial", stdout=StringIO(), stderr=StringIO()
        )
        call_command(
            "popular_catalogo_inicial", stdout=StringIO(), stderr=StringIO()
        )

        self.assertEqual(buscar.call_count, len(TERMOS_INICIAIS))
        self.assertEqual(Produto.objects.count(), 12 * len(TERMOS_INICIAIS))
        self.assertEqual(Preco.objects.count(), 12 * len(TERMOS_INICIAIS))

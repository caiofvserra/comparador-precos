from unittest.mock import patch

from django.test import SimpleTestCase


class ConfiguracaoCatalogoTests(SimpleTestCase):
    def test_render_em_modo_triangulacao_prioriza_tres_redes(self):
        with patch.dict("os.environ", {"CATALOGO_MODO": "triangulacao"}):
            resposta = self.client.get("/api/v1/configuracao/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {
            "modo": "triangulacao",
            "min_redes_padrao": 3,
        })
        self.assertEqual(resposta["Cache-Control"], "no-store")

    def test_instalacao_completa_nao_limita_catalogo(self):
        with patch.dict("os.environ", {"CATALOGO_MODO": "completo"}):
            resposta = self.client.get("/api/v1/configuracao/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {
            "modo": "completo",
            "min_redes_padrao": 0,
        })

    def test_modo_invalido_faz_fallback_para_completo(self):
        with patch.dict("os.environ", {"CATALOGO_MODO": "invalido"}):
            resposta = self.client.get("/api/v1/configuracao/")
        self.assertEqual(resposta.json()["min_redes_padrao"], 0)

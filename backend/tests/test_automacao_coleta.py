"""Verifica autorização e execução assíncrona do coletor."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from coleta.models import ExecucaoColeta


URL = "/api/v1/interno/coleta/"
CLAIMS = {"event_name": "workflow_dispatch"}


class ColetaAgendadaAPITests(TestCase):
    def test_sem_oidc_recusa_acesso(self):
        resposta = self.client.post(URL)
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(ExecucaoColeta.objects.count(), 0)

    @patch("coleta.automacao.subprocess.Popen")
    @patch("coleta.automacao.autenticar_github", return_value=CLAIMS)
    def test_aciona_coleta_e_retorna_execucao(self, auth, processo):
        resposta = self.client.post(URL)
        self.assertEqual(resposta.status_code, 202)
        self.assertEqual(ExecucaoColeta.objects.count(), 1)
        processo.assert_called_once()
        detalhes = self.client.get(
            URL + str(resposta.json()["id"]) + "/"
        )
        self.assertEqual(detalhes.status_code, 200)
        self.assertEqual(detalhes.json()["estado"], "pendente")
        self.assertEqual(detalhes.json()["novos_registros"], 0)

    @patch("coleta.automacao.subprocess.Popen")
    @patch("coleta.automacao.autenticar_github", return_value=CLAIMS)
    def test_repeticao_durante_coleta_nao_dispara_duas_vezes(self, auth, processo):
        primeira = self.client.post(URL)
        segunda = self.client.post(URL)
        self.assertEqual(primeira.json()["id"], segunda.json()["id"])
        processo.assert_called_once()

    @patch("coleta.automacao.subprocess.Popen", side_effect=OSError("falha de sistema"))
    @patch("coleta.automacao.autenticar_github", return_value=CLAIMS)
    def test_falha_inicio_fica_registrada(self, auth, processo):
        resposta = self.client.post(URL)
        self.assertEqual(resposta.status_code, 500)
        self.assertEqual(
            ExecucaoColeta.objects.first().estado, ExecucaoColeta.Estados.ERRO
        )

    @patch("coleta.automacao.autenticar_github", return_value=CLAIMS)
    def test_consulta_detecta_processo_encerrado_por_deploy(self, auth):
        execucao = ExecucaoColeta.objects.create(
            origem="schedule",
            estado=ExecucaoColeta.Estados.EXECUTANDO,
        )
        antigo = timezone.now() - timedelta(minutes=5)
        ExecucaoColeta.objects.filter(pk=execucao.pk).update(
            iniciada_em=antigo,
            ultima_atividade_em=antigo,
        )
        resposta = self.client.get(f"{URL}{execucao.pk}/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["estado"], "erro")
        self.assertIn("interrompida", resposta.json()["erro"])
        execucao.refresh_from_db()
        self.assertIsNotNone(execucao.finalizada_em)

    @patch("coleta.automacao.subprocess.Popen")
    @patch("coleta.automacao.autenticar_github", return_value=CLAIMS)
    def test_nova_coleta_apos_processo_interrompido(self, auth, processo):
        anterior = ExecucaoColeta.objects.create(
            origem="schedule",
            estado=ExecucaoColeta.Estados.EXECUTANDO,
        )
        antigo = timezone.now() - timedelta(minutes=5)
        ExecucaoColeta.objects.filter(pk=anterior.pk).update(
            iniciada_em=antigo,
            ultima_atividade_em=antigo,
        )
        resposta = self.client.post(URL)
        self.assertEqual(resposta.status_code, 202)
        self.assertNotEqual(resposta.json()["id"], anterior.pk)
        anterior.refresh_from_db()
        self.assertEqual(anterior.estado, ExecucaoColeta.Estados.ERRO)
        processo.assert_called_once()

    @patch("coleta.automacao.subprocess.Popen")
    @patch("coleta.automacao.autenticar_github", return_value=CLAIMS)
    def test_pulso_recente_preserva_execucao_ativa(self, auth, processo):
        execucao = ExecucaoColeta.objects.create(
            origem="schedule",
            estado=ExecucaoColeta.Estados.EXECUTANDO,
            ultima_atividade_em=timezone.now(),
        )
        ExecucaoColeta.objects.filter(pk=execucao.pk).update(
            iniciada_em=timezone.now() - timedelta(minutes=10),
        )
        resposta = self.client.post(URL)
        self.assertEqual(resposta.status_code, 202)
        self.assertEqual(resposta.json()["id"], execucao.pk)
        processo.assert_not_called()

    @patch("coleta.automacao.jwt.decode")
    @patch("coleta.automacao.JWK_CLIENT.get_signing_key_from_jwt")
    def test_oidc_de_outro_workflow_e_rejeitado(self, chave, decode):
        from types import SimpleNamespace
        from django.test import RequestFactory
        from coleta.automacao import autenticar_github
        chave.return_value = SimpleNamespace(key="key")
        decode.return_value = {
            "repository": "caiofvserra/comparador-precos",
            "ref": "refs/heads/main",
            "workflow_ref": "outro/workflow.yml",
            "event_name": "push",
        }
        req = RequestFactory().post(URL, HTTP_AUTHORIZATION="Bearer valido")
        self.assertIsNone(autenticar_github(req))

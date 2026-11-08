from datetime import datetime, timezone as tz
from types import SimpleNamespace
from django.test import SimpleTestCase
from coleta.registro_diario import precisa_observar_hoje


class RegistroDiarioTest(SimpleTestCase):
    def test_registra_novo_dia_em_sao_paulo(self):
        anterior = SimpleNamespace(data_hora_coleta=datetime(2026, 11, 7, 17, tzinfo=tz.utc))
        atual = datetime(2026, 11, 8, 17, tzinfo=tz.utc)
        self.assertTrue(precisa_observar_hoje(anterior, atual))

    def test_nao_duplica_observacao_mesmo_dia(self):
        anterior = SimpleNamespace(data_hora_coleta=datetime(2026, 11, 8, 13, tzinfo=tz.utc))
        atual = datetime(2026, 11, 8, 20, tzinfo=tz.utc)
        self.assertFalse(precisa_observar_hoje(anterior, atual))

    def test_respeita_fuso_do_brasil_na_virada_utc(self):
        anterior = SimpleNamespace(data_hora_coleta=datetime(2026, 11, 8, 23, 59, tzinfo=tz.utc))
        atual = datetime(2026, 11, 9, 1, tzinfo=tz.utc)
        self.assertFalse(precisa_observar_hoje(anterior, atual))

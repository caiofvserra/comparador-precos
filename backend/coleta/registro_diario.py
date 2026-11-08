"""Registra uma nova observação de preço no máximo uma vez por dia local.

A cotação precisa ser lida novamente da fonte; nunca replicamos preços
antigos sem consulta externa. A função só decide sobre observação inalterada.
"""
from zoneinfo import ZoneInfo
from django.utils import timezone

FUSO = ZoneInfo("America/Sao_Paulo")


def precisa_observar_hoje(ultimo, agora=None):
    if ultimo is None:
        return True
    momento = agora if agora is not None else timezone.now()
    return ultimo.data_hora_coleta.astimezone(FUSO).date() < momento.astimezone(FUSO).date()

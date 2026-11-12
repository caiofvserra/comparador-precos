"""Executa a coleta no Render e salva o resultado consultável pelo Actions.

O sinal de vida permite reconhecer uma coleta interrompida por redeploy.
"""

import logging
from threading import Event, Thread

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, close_old_connections, connections
from django.utils import timezone

from coleta.models import ExecucaoColeta


# Chave fixa somente para exclusão mútua no banco do comparador.
PG_LOCK = (2026, 1110)
LOGGER = logging.getLogger(__name__)
PULSO_SEGUNDOS = 20


def registrar_pulsos(execucao_id, parar):
    """Atualiza o banco em outra conexão, mesmo durante consultas demoradas."""
    try:
        while not parar.wait(PULSO_SEGUNDOS):
            try:
                close_old_connections()
                atualizados = ExecucaoColeta.objects.filter(
                    pk=execucao_id,
                    estado=ExecucaoColeta.Estados.EXECUTANDO,
                ).update(ultima_atividade_em=timezone.now())
                if not atualizados:
                    return
            except Exception:
                LOGGER.exception(
                    "[coleta-agendada] Não foi possível renovar pulso da execução %s.",
                    execucao_id,
                )
    finally:
        connections.close_all()


class Command(BaseCommand):
    help = "Executa a atualização real diária de três redes com trava e auditoria."

    def add_arguments(self, parser):
        parser.add_argument("--execucao-id", type=int, required=True)

    def handle(self, *args, **options):
        execucao = ExecucaoColeta.objects.get(pk=options["execucao_id"])
        travou = False
        parar = Event()
        thread = None
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_try_advisory_lock(%s, %s)", PG_LOCK)
                travou = bool(cursor.fetchone()[0])
            if not travou:
                raise CommandError("Outra atualização está em andamento.")

            execucao.estado = ExecucaoColeta.Estados.EXECUTANDO
            execucao.ultima_atividade_em = timezone.now()
            execucao.save(update_fields=["estado", "ultima_atividade_em"])

            thread = Thread(
                target=registrar_pulsos,
                args=(execucao.pk, parar),
                name=f"pulso-coleta-{execucao.pk}",
                daemon=True,
            )
            thread.start()

            self.stdout.write(
                f"[coleta-agendada] Execução {execucao.pk} iniciada: "
                "Savegnago, Atacadão e Carrefour."
            )
            call_command(
                "atualizar_precos_todos",
                cep="14010000",
                gravar=True,
                registrar_observacoes=True,
            )
            # Não sobrescreve erro já registrado pelo monitor.
            ExecucaoColeta.objects.filter(
                pk=execucao.pk,
                estado=ExecucaoColeta.Estados.EXECUTANDO,
            ).update(
                estado=ExecucaoColeta.Estados.CONCLUIDA,
                finalizada_em=timezone.now(),
            )
            self.stdout.write(
                f"[coleta-agendada] Execução {execucao.pk} concluída."
            )
        except Exception as exc:
            ExecucaoColeta.objects.filter(
                pk=execucao.pk,
                estado__in=[
                    ExecucaoColeta.Estados.PENDENTE,
                    ExecucaoColeta.Estados.EXECUTANDO,
                ],
            ).update(
                estado=ExecucaoColeta.Estados.ERRO,
                erro=str(exc)[:1500],
                finalizada_em=timezone.now(),
            )
            self.stderr.write(
                f"[coleta-agendada] Execução {execucao.pk} falhou: {exc}"
            )
            raise
        finally:
            parar.set()
            if thread is not None:
                thread.join(timeout=5)
            if travou:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(%s, %s)", PG_LOCK)

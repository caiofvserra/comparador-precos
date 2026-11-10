"""Executa a coleta no Render e salva o resultado consultável pelo Actions."""

from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection
from django.utils import timezone

from coleta.models import ExecucaoColeta


# Chave fixa somente para exclusão mútua no banco do comparador.
PG_LOCK = (2026, 1110)


class Command(BaseCommand):
    help = "Executa a atualização real diária de três redes com trava e auditoria."

    def add_arguments(self, parser):
        parser.add_argument("--execucao-id", type=int, required=True)

    def handle(self, *args, **options):
        execucao = ExecucaoColeta.objects.get(pk=options["execucao_id"])
        travou = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_try_advisory_lock(%s, %s)", PG_LOCK)
                travou = bool(cursor.fetchone()[0])
            if not travou:
                raise CommandError("Outra atualização está em andamento.")

            execucao.estado = ExecucaoColeta.Estados.EXECUTANDO
            execucao.save(update_fields=["estado"])
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
            execucao.estado = ExecucaoColeta.Estados.CONCLUIDA
            self.stdout.write(
                f"[coleta-agendada] Execução {execucao.pk} concluída."
            )
        except Exception as exc:
            execucao.estado = ExecucaoColeta.Estados.ERRO
            execucao.erro = str(exc)[:1500]
            self.stderr.write(
                f"[coleta-agendada] Execução {execucao.pk} falhou: {exc}"
            )
            raise
        finally:
            execucao.finalizada_em = timezone.now()
            execucao.save(update_fields=["estado", "erro", "finalizada_em"])
            if travou:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(%s, %s)", PG_LOCK)

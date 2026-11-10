"""Registro da atualização de preços acionada pelo GitHub Actions."""

from django.db import models


class ExecucaoColeta(models.Model):
    class Estados(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EXECUTANDO = "executando", "Executando"
        CONCLUIDA = "concluida", "Concluída"
        ERRO = "erro", "Erro"

    estado = models.CharField(
        max_length=16, choices=Estados.choices, default=Estados.PENDENTE
    )
    origem = models.CharField(max_length=32, default="schedule")
    iniciada_em = models.DateTimeField(auto_now_add=True)
    finalizada_em = models.DateTimeField(null=True, blank=True)
    erro = models.TextField(blank=True)

    class Meta:
        ordering = ["-iniciada_em"]

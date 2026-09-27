from django.core.exceptions import ValidationError
from django.db import models

from catalogo.models import Produto, Supermercado


class OfertaFonte(models.Model):
    """Item encontrado na fonte online de um supermercado, mapeado para um Produto."""

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="ofertas")
    supermercado = models.ForeignKey(
        Supermercado, on_delete=models.CASCADE, related_name="ofertas"
    )
    codigo_externo = models.CharField(max_length=50, blank=True)
    nome_externo = models.CharField(max_length=200)
    url_fonte = models.URLField()
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome_externo} - {self.supermercado}"

    def clean(self):
        # RN-10: só pode existir uma oferta ativa por produto + supermercado
        if self.ativo and self.produto_id and self.supermercado_id:
            outras_ativas = OfertaFonte.objects.filter(
                produto_id=self.produto_id, supermercado_id=self.supermercado_id, ativo=True
            ).exclude(pk=self.pk)
            if outras_ativas.exists():
                raise ValidationError(
                    "Já existe uma oferta ativa para este produto neste supermercado."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Preco(models.Model):
    """Registro de preço coletado. Nunca é sobrescrito, forma o histórico."""

    oferta_fonte = models.ForeignKey(
        OfertaFonte, on_delete=models.CASCADE, related_name="precos"
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_hora_coleta = models.DateTimeField()

    class Meta:
        ordering = ["-data_hora_coleta"]

    def __str__(self):
        return f"{self.oferta_fonte} - R$ {self.valor} ({self.data_hora_coleta:%d/%m/%Y %H:%M})"

    def clean(self):
        # RN-09: preço zero ou negativo não é publicado
        if self.valor is not None and self.valor <= 0:
            raise ValidationError({"valor": "O valor deve ser maior que zero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

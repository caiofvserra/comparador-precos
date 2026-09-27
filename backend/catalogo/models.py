from django.db import models


class Supermercado(models.Model):
    nome = models.CharField(max_length=100)
    endereco = models.CharField(max_length=200)
    complemento = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    site_url = models.URLField()
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    nome = models.CharField(max_length=100)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Produto(models.Model):
    """Produto canônico, usado para comparar itens entre supermercados."""

    nome = models.CharField(max_length=200)
    marca = models.CharField(max_length=100, blank=True)
    codigo_barras = models.CharField(max_length=20, blank=True, null=True)
    categorias = models.ManyToManyField(Categoria, blank=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        if self.marca:
            return f"{self.nome} ({self.marca})"
        return self.nome

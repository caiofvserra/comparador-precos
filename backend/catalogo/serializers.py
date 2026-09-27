from rest_framework import serializers

from .models import Produto, Supermercado


class SupermercadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supermercado
        fields = ["id", "nome", "cidade", "site_url"]


class SupermercadoResumoSerializer(serializers.ModelSerializer):
    """Versão curta usada dentro de comparação, histórico e simulação."""

    class Meta:
        model = Supermercado
        fields = ["id", "nome"]


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ["id", "nome", "marca", "codigo_barras"]

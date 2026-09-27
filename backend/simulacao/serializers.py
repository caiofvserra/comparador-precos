from rest_framework import serializers

from catalogo.models import Produto
from catalogo.serializers import SupermercadoResumoSerializer


# ---- entrada ----

class ItemListaSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1, max_value=1000)

    def validate_produto_id(self, valor):
        if not Produto.objects.filter(pk=valor).exists():
            raise serializers.ValidationError(f"Produto {valor} não existe.")
        return valor


class ListaSerializer(serializers.Serializer):
    itens = ItemListaSerializer(many=True, allow_empty=False)


# ---- saída ----

class ItemResultadoSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField()
    valor_unitario = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)


class ResultadoSupermercadoSerializer(serializers.Serializer):
    supermercado = SupermercadoResumoSerializer()
    status = serializers.CharField()
    itens_encontrados = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    itens = ItemResultadoSerializer(many=True)
    itens_ausentes = serializers.ListField(child=serializers.IntegerField())


class SimulacaoSerializer(serializers.Serializer):
    total_itens = serializers.IntegerField()
    supermercados = ResultadoSupermercadoSerializer(many=True)

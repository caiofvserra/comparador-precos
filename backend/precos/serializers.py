from rest_framework import serializers

from catalogo.serializers import ProdutoSerializer, SupermercadoResumoSerializer


class PrecoComparacaoSerializer(serializers.Serializer):
    supermercado = SupermercadoResumoSerializer()
    disponivel = serializers.BooleanField()
    valor = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    data_hora_coleta = serializers.DateTimeField(allow_null=True)
    url_fonte = serializers.URLField(allow_null=True)


class ComparacaoSerializer(serializers.Serializer):
    produto = ProdutoSerializer()
    precos = PrecoComparacaoSerializer(many=True)


class PrecoHistoricoSerializer(serializers.Serializer):
    supermercado = SupermercadoResumoSerializer(source="oferta_fonte.supermercado")
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)
    data_hora_coleta = serializers.DateTimeField()
    url_fonte = serializers.URLField(source="oferta_fonte.url_fonte")


class HistoricoSerializer(serializers.Serializer):
    produto = ProdutoSerializer()
    historico = PrecoHistoricoSerializer(many=True)

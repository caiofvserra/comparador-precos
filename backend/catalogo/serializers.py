from rest_framework import serializers

from .models import Produto, Supermercado


class SupermercadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supermercado
        fields = ["id", "nome", "cidade", "site_url"]


class SupermercadoResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supermercado
        fields = ["id", "nome", "site_url"]


class ProdutoSerializer(serializers.ModelSerializer):
    categorias = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="nome",
    )
    preco_minimo = serializers.SerializerMethodField()
    preco_maximo = serializers.SerializerMethodField()
    quantidade_redes = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = [
            "id",
            "nome",
            "marca",
            "codigo_barras",
            "imagem_url",
            "categorias",
            "preco_minimo",
            "preco_maximo",
            "quantidade_redes",
        ]

    def get_quantidade_redes(self, produto):
        if hasattr(produto, "quantidade_redes"):
            return produto.quantidade_redes
        return (
            produto.ofertas.filter(
                ativo=True,
                supermercado__ativo=True,
                precos__isnull=False,
            )
            .values("supermercado_id")
            .distinct()
            .count()
        )

    def _valores_atuais(self, produto):
        valores = []

        ofertas = produto.ofertas.filter(
            ativo=True,
            supermercado__ativo=True,
        )

        for oferta in ofertas:
            preco = oferta.precos.order_by("-data_hora_coleta").first()

            if preco:
                valores.append(preco.valor)

        return valores

    def get_preco_minimo(self, produto):
        valores = self._valores_atuais(produto)

        if not valores:
            return None

        return f"{min(valores):.2f}"

    def get_preco_maximo(self, produto):
        valores = self._valores_atuais(produto)

        if not valores:
            return None

        return f"{max(valores):.2f}"
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogo.models import Produto

from .serializers import ComparacaoSerializer, HistoricoSerializer
from .services import comparar_produto, historico_produto


class ComparacaoView(APIView):
    """RF-03/RF-04: preço mais recente do produto em cada supermercado."""

    def get(self, request, produto_id):
        produto = get_object_or_404(Produto, pk=produto_id)
        dados = {"produto": produto, "precos": comparar_produto(produto)}
        return Response(ComparacaoSerializer(dados).data)


class HistoricoView(APIView):
    """RF-09: histórico de preços do produto, com filtro opcional por supermercado."""

    def get(self, request, produto_id):
        produto = get_object_or_404(Produto, pk=produto_id)

        supermercado_id = request.query_params.get("supermercado_id", "").strip()
        if supermercado_id and not supermercado_id.isdigit():
            return Response(
                {"supermercado_id": "Informe um número inteiro."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dados = {"produto": produto, "historico": historico_produto(produto, supermercado_id)}
        return Response(HistoricoSerializer(dados).data)

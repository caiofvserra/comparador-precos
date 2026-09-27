from django.db.models import Q
from rest_framework.generics import ListAPIView

from .models import Produto, Supermercado
from .serializers import ProdutoSerializer, SupermercadoSerializer


class ProdutoListView(ListAPIView):
    """RF-01: busca de produtos por nome ou marca. Sem `q` retorna todos."""

    serializer_class = ProdutoSerializer

    def get_queryset(self):
        produtos = Produto.objects.all()
        q = self.request.query_params.get("q", "").strip()
        if q:
            produtos = produtos.filter(Q(nome__icontains=q) | Q(marca__icontains=q))
        return produtos


class SupermercadoListView(ListAPIView):
    """RF-02: lista os supermercados ativos."""

    serializer_class = SupermercadoSerializer
    queryset = Supermercado.objects.filter(ativo=True)

from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView

from .models import Produto, Supermercado
from .serializers import ProdutoSerializer, SupermercadoSerializer


class ProdutoListView(ListAPIView):
    """RF-01: busca por nome ou marca; filtro opcional por redes com preço."""

    serializer_class = ProdutoSerializer

    def get_queryset(self):
        produtos = Produto.objects.annotate(
            quantidade_redes=Count(
                "ofertas__supermercado_id",
                filter=Q(
                    ofertas__ativo=True,
                    ofertas__supermercado__ativo=True,
                    ofertas__precos__isnull=False,
                ),
                distinct=True,
            ),
        )
        q = self.request.query_params.get("q", "").strip()
        if q:
            produtos = produtos.filter(
                Q(nome__icontains=q) | Q(marca__icontains=q)
            )

        minimo = self.request.query_params.get("min_redes")
        if minimo is not None:
            if minimo not in ("0", "1", "2", "3"):
                raise ValidationError({
                    "min_redes": "Informe 0, 1, 2 ou 3."
                })
            if minimo != "0":
                produtos = produtos.filter(
                    quantidade_redes__gte=int(minimo)
                )

        if self.request.query_params.get("priorizar_redes") == "1":
            return produtos.order_by("-quantidade_redes", "nome")
        return produtos.order_by("nome")


class SupermercadoListView(ListAPIView):
    """RF-02: lista os supermercados ativos."""

    serializer_class = SupermercadoSerializer
    queryset = Supermercado.objects.filter(ativo=True)

from django.urls import path

from .views import ProdutoListView, SupermercadoListView

urlpatterns = [
    path("produtos/", ProdutoListView.as_view(), name="produto-lista"),
    path("supermercados/", SupermercadoListView.as_view(), name="supermercado-lista"),
]

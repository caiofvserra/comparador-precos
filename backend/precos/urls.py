from django.urls import path

from .views import ComparacaoView, HistoricoView

urlpatterns = [
    path(
        "produtos/<int:produto_id>/comparacao/",
        ComparacaoView.as_view(),
        name="produto-comparacao",
    ),
    path(
        "produtos/<int:produto_id>/historico/",
        HistoricoView.as_view(),
        name="produto-historico",
    ),
]

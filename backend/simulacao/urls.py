from django.urls import path

from .views import SimularListaView

urlpatterns = [
    path("listas/simular/", SimularListaView.as_view(), name="lista-simular"),
]

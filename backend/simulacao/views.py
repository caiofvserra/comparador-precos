from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ListaSerializer, SimulacaoSerializer
from .services import simular_lista


class SimularListaView(APIView):
    """RF-06/RF-07: calcula o total previsto da lista em cada supermercado."""

    def post(self, request):
        entrada = ListaSerializer(data=request.data)
        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)

        resultado = simular_lista(entrada.validated_data["itens"])
        return Response(SimulacaoSerializer(resultado).data)

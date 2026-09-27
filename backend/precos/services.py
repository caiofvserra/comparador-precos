"""Regras de negócio de preços: preço atual e comparação entre supermercados."""

from catalogo.models import Supermercado

from .models import OfertaFonte, Preco


def preco_atual(oferta):
    """RN-01: o preço atual é o registro mais recente por data_hora_coleta."""
    return oferta.precos.order_by("-data_hora_coleta").first()


def oferta_ativa(produto, supermercado):
    """RN-10 garante no máximo uma oferta ativa por produto + supermercado."""
    return OfertaFonte.objects.filter(
        produto=produto, supermercado=supermercado, ativo=True
    ).first()


def comparar_produto(produto):
    """
    Monta a lista de preços atuais do produto, um item por supermercado ativo.
    Supermercado sem oferta ou sem preço aparece com disponivel=False (CT-04).
    """
    resultado = []
    for supermercado in Supermercado.objects.filter(ativo=True):
        item = {
            "supermercado": supermercado,
            "disponivel": False,
            "valor": None,
            "data_hora_coleta": None,
            "url_fonte": None,
        }

        oferta = oferta_ativa(produto, supermercado)
        preco = preco_atual(oferta) if oferta else None
        if preco:
            item["disponivel"] = True
            item["valor"] = preco.valor
            item["data_hora_coleta"] = preco.data_hora_coleta
            item["url_fonte"] = oferta.url_fonte

        resultado.append(item)
    return resultado


def historico_produto(produto, supermercado_id=None):
    """RF-09: todos os preços coletados do produto, do mais antigo ao mais recente."""
    precos = Preco.objects.filter(oferta_fonte__produto=produto)
    if supermercado_id:
        precos = precos.filter(oferta_fonte__supermercado_id=supermercado_id)
    return precos.select_related("oferta_fonte__supermercado").order_by("data_hora_coleta")

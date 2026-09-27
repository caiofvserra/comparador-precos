"""Regra da lista de compras: total previsto por supermercado."""

from decimal import Decimal

from catalogo.models import Supermercado
from precos.services import oferta_ativa, preco_atual


def simular_lista(itens):
    """
    Recebe [{"produto_id": 101, "quantidade": 2}, ...] e calcula, para cada
    supermercado ativo, o total usando o preço atual de cada item (RN-05).
    Se faltar preço para algum item o resultado fica "incompleto" (RN-06).
    """
    resultado = []
    for supermercado in Supermercado.objects.filter(ativo=True):
        total = Decimal("0.00")
        itens_com_preco = []
        itens_ausentes = []

        for item in itens:
            oferta = oferta_ativa(item["produto_id"], supermercado)
            preco = preco_atual(oferta) if oferta else None
            if preco:
                subtotal = preco.valor * item["quantidade"]
                total += subtotal
                itens_com_preco.append({
                    "produto_id": item["produto_id"],
                    "quantidade": item["quantidade"],
                    "valor_unitario": preco.valor,
                    "subtotal": subtotal,
                })
            else:
                itens_ausentes.append(item["produto_id"])

        resultado.append({
            "supermercado": supermercado,
            "status": "completo" if not itens_ausentes else "incompleto",
            "itens_encontrados": len(itens_com_preco),
            "total": total,
            "itens": itens_com_preco,
            "itens_ausentes": itens_ausentes,
        })

    return {"total_itens": len(itens), "supermercados": resultado}

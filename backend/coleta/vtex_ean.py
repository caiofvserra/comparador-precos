"""Consulta pública de SKU VTEX por EAN, mantendo sessão regionalizada.

O filtro alternateIds_Ean é testado primeiro; caso não seja aceito pela loja,
recorre à busca textual, SEM aceitar um resultado com EAN diferente.
Nenhuma função deste módulo grava no banco.
"""

from coleta.atacadao import URL_BUSCA as URL_ATACADAO
from coleta.savegnago import URL_BUSCA as URL_SAVEGNAGO


CONFIG = {
    "Savegnago": {
        "url": URL_SAVEGNAGO,
        "dominio": "https://www.savegnago.com.br/",
        "vendedor": "SAVEGNAGO",
    },
    "Atacadão": {
        "url": URL_ATACADAO,
        "dominio": "https://www.atacadao.com.br/",
        "vendedor": "ATACADAO",
    },
}


def buscar_ean(loja, ean, sessao):
    """Busca um EAN exato e devolve oferta real disponível ou None."""
    if loja not in CONFIG:
        raise ValueError("Rede não suportada para consulta VTEX.")
    ean = str(ean).strip()
    if not ean.isdigit() or len(ean) not in (8, 12, 13, 14):
        return None

    config = CONFIG[loja]
    for parametros in (
        {"fq": f"alternateIds_Ean:{ean}", "_from": 0, "_to": 9},
        {"ft": ean, "_from": 0, "_to": 9},
    ):
        resposta = sessao.get(
            config["url"], params=parametros, timeout=20
        )
        if resposta.status_code in (400, 404, 422):
            continue
        resposta.raise_for_status()
        dados = resposta.json()
        if not isinstance(dados, list):
            continue

        for produto in dados:
            if not isinstance(produto, dict):
                continue
            url = str(produto.get("link") or "").strip()
            if not url.startswith(config["dominio"]):
                continue
            for sku in produto.get("items") or []:
                if str(sku.get("ean") or "").strip() != ean:
                    continue
                for vendedor in sku.get("sellers") or []:
                    if config["vendedor"] not in str(
                        vendedor.get("sellerName") or ""
                    ).upper():
                        continue
                    comercial = vendedor.get("commertialOffer") or {}
                    if (
                        comercial.get("IsAvailable") is not True
                        or comercial.get("AvailableQuantity", 0) <= 0
                    ):
                        continue
                    imagens = sku.get("images") or []
                    imagem = (
                        str(imagens[0].get("imageUrl") or "").strip()
                        if imagens and isinstance(imagens[0], dict) else ""
                    )
                    return {
                        "nome": produto.get("productName") or "",
                        "marca": produto.get("brand") or "",
                        "codigo_barras": ean,
                        "sku": str(sku.get("itemId") or ""),
                        "vendedor_nome": vendedor.get("sellerName") or "",
                        "preco": comercial.get("Price"),
                        "disponivel": True,
                        "url": url,
                        "imagem_url": imagem,
                    }
    return None

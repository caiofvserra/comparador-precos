"""Varredura regionalizada e paginada das APIs públicas VTEX.

A busca antiga inspecionava somente o primeiro SKU de cada produto. Este
módulo considera cada SKU com EAN, vendedor e oferta válida, sem gravar nada.
"""

import os
import unicodedata
from urllib.parse import urlparse, urlunparse

from coleta.atacadao import URL_BUSCA as ATACADAO_URL
from coleta.savegnago import URL_BUSCA as SAVEGNAGO_URL
from coleta.management.commands.triangular_precos import normalizar_oferta


URLS = {
    "Savegnago": SAVEGNAGO_URL,
    "Atacadão": ATACADAO_URL,
}
VENDEDORES = {"Savegnago": "SAVEGNAGO", "Atacadão": "ATACADAO"}


def _ascii_maiusculo(texto):
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(texto or ""))
        if not unicodedata.combining(c)
    ).upper()


def _url_oficial(url, loja):
    parsed = urlparse(str(url or ""))
    if parsed.scheme != "https":
        return ""
    host = parsed.netloc.casefold()
    oficial = "atacadao.com.br" if loja == "Atacadão" else "savegnago.com.br"
    permitidos = {oficial, "www." + oficial}
    if loja == "Atacadão":
        permitidos.add("secure.atacadao.com.br")
    if host not in permitidos:
        return ""
    # Preserva o domínio real da fonte para o link de comprovação da oferta.
    destino = host if host == "secure.atacadao.com.br" else "www." + oficial
    return urlunparse(parsed._replace(netloc=destino))


def _amostra_diagnostico(dados, loja, termo):
    if loja != "Atacadão" or os.environ.get("VTEX_DIAGNOSTICO") != "true":
        return
    diagnosticos = []
    for produto in dados[:2]:
        itens = produto.get("items") or []
        diagnosticos.append({
            "host_link": urlparse(produto.get("link") or "").netloc,
            "qtd_skus": len(itens),
            "skus": [
                {
                    "ean_preenchido": bool(str(sku.get("ean") or "").strip()),
                    "vendedores": [
                        {
                            "nome": vendedor.get("sellerName"),
                            "disponivel": (vendedor.get("commertialOffer") or {}).get(
                                "IsAvailable"
                            ),
                            "estoque": (vendedor.get("commertialOffer") or {}).get(
                                "AvailableQuantity"
                            ),
                            "preco_preenchido": (
                                (vendedor.get("commertialOffer") or {}).get("Price") is not None
                            ),
                        }
                        for vendedor in (sku.get("sellers") or [])[:3]
                    ],
                } for sku in itens[:2]
            ],
        })
    print(f"[vtex-diagnostico] Atacadão {termo}: {diagnosticos}", flush=True)


def extrair_skus(produtos, loja):
    """Devolve todas as variantes disponíveis, não só items[0]."""
    if loja not in URLS:
        raise ValueError("Supermercado VTEX não suportado.")
    resultado = {}
    for produto in produtos:
        if not isinstance(produto, dict):
            continue
        url = _url_oficial(produto.get("link"), loja)
        for sku in produto.get("items") or []:
            if not isinstance(sku, dict):
                continue
            vendedores = sku.get("sellers") or []
            for vendedor in vendedores:
                if VENDEDORES[loja] not in _ascii_maiusculo(
                    vendedor.get("sellerName")
                ):
                    continue
                oferta = vendedor.get("commertialOffer") or {}
                if (
                    oferta.get("IsAvailable") is not True
                    or oferta.get("AvailableQuantity", 0) <= 0
                ):
                    continue
                imagens = sku.get("images") or []
                imagem = (
                    imagens[0].get("imageUrl") or ""
                    if imagens and isinstance(imagens[0], dict) else ""
                )
                item = {
                    "nome": sku.get("name") or produto.get("productName") or "",
                    "marca": produto.get("brand") or "",
                    "codigo_barras": sku.get("ean"),
                    "sku": sku.get("itemId"),
                    "vendedor_nome": _ascii_maiusculo(
                        vendedor.get("sellerName")
                    ),
                    "preco": oferta.get("Price"),
                    "disponivel": True,
                    "url": url,
                    "imagem_url": imagem,
                }
                normalizado = normalizar_oferta(item, loja)
                if normalizado:
                    resultado[normalizado["ean"]] = normalizado
                break
    return resultado


def buscar_paginado(loja, termo, sessao, paginas=3, tamanho=30):
    """Consulta até paginas páginas e devolve EANs distintos com preço."""
    if loja not in URLS:
        raise ValueError("Loja desconhecida.")
    if not 1 <= paginas <= 8 or not 1 <= tamanho <= 40:
        raise ValueError("Limites de paginação inválidos.")

    ofertas = {}
    for pagina in range(paginas):
        inicio = pagina * tamanho
        resposta = sessao.get(
            URLS[loja],
            params={"ft": termo, "_from": inicio, "_to": inicio + tamanho - 1},
            timeout=25,
        )
        if resposta.status_code in (400, 404, 422):
            break
        resposta.raise_for_status()
        dados = resposta.json()
        if not isinstance(dados, list):
            raise ValueError("Catálogo VTEX retornou formato inválido.")
        if not dados:
            break
        if pagina == 0:
            _amostra_diagnostico(dados, loja, termo)
        ofertas.update(extrair_skus(dados, loja))
        if len(dados) < tamanho:
            break
    return ofertas

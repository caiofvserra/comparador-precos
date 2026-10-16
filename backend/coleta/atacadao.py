import requests


URL_BASE = "https://www.atacadao.com.br"
URL_SESSOES = f"{URL_BASE}/api/sessions"
URL_BUSCA = f"{URL_BASE}/io/api/catalog_system/pub/products/search"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def criar_sessao(cep="14010000"):
    """Cria uma sessão regionalizada para o CEP informado."""
    cep = "".join(c for c in str(cep) if c.isdigit())

    if len(cep) != 8:
        raise ValueError("Informe um CEP válido com 8 dígitos.")

    sessao = requests.Session()
    sessao.headers.update({
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    })

    resposta = sessao.post(
        URL_SESSOES,
        json={
            "public": {
                "country": {"value": "BRA"},
                "postalCode": {"value": cep},
            }
        },
        timeout=30,
    )
    resposta.raise_for_status()
    return sessao


def buscar_produtos(termo="leite", quantidade=10, cep="14010000"):
    """
    Consulta produtos no catálogo público do Atacadão.
    Não grava nada no banco de dados.
    """
    if not str(termo).strip():
        raise ValueError("Informe um termo para a busca.")

    if not 1 <= quantidade <= 50:
        raise ValueError("A quantidade deve estar entre 1 e 50.")

    sessao = criar_sessao(cep)
    produtos = []
    ids_vistos = set()
    inicio = 0
    tamanho_pagina = min(10, quantidade)

    while len(produtos) < quantidade:
        fim = inicio + tamanho_pagina - 1

        resposta = sessao.get(
            URL_BUSCA,
            params={
                "ft": str(termo).strip(),
                "_from": inicio,
                "_to": fim,
            },
            timeout=30,
        )
        resposta.raise_for_status()

        dados = resposta.json()
        if not isinstance(dados, list):
            raise ValueError("A API do Atacadão retornou formato inesperado.")

        if not dados:
            break

        for produto in dados:
            product_id = str(produto.get("productId") or "").strip()

            if not product_id or product_id in ids_vistos:
                continue

            ids_vistos.add(product_id)

            itens = produto.get("items") or []
            item = itens[0] if itens else {}
            vendedores = item.get("sellers") or []

            vendedor = next(
                (
                    v for v in vendedores
                    if "ATACADAO" in str(
                        v.get("sellerName") or ""
                    ).upper()
                    and (v.get("commertialOffer") or {}).get(
                        "IsAvailable", False
                    )
                    and (v.get("commertialOffer") or {}).get(
                        "AvailableQuantity", 0
                    ) > 0
                    and (v.get("commertialOffer") or {}).get(
                        "Price", 0
                    ) > 0
                ),
                None,
            )

            if vendedor is None:
                oferta = {}
                disponivel = False
                vendedor_id = ""
                vendedor_nome = ""
            else:
                oferta = vendedor.get("commertialOffer") or {}
                disponivel = bool(
                    oferta.get("IsAvailable", False)
                    and oferta.get("AvailableQuantity", 0) > 0
                    and oferta.get("Price", 0) > 0
                )
                vendedor_id = str(vendedor.get("sellerId") or "")
                vendedor_nome = str(vendedor.get("sellerName") or "")

            ean = str(item.get("ean") or "").strip()
            if ean == "0":
                ean = ""

            produtos.append({
                "id_externo": product_id,
                "sku": str(item.get("itemId") or ""),
                "vendedor_id": vendedor_id,
                "vendedor_nome": vendedor_nome,
                "nome": produto.get("productName") or "",
                "marca": produto.get("brand") or "",
                "codigo_barras": ean,
                "preco": oferta.get("Price"),
                "disponivel": disponivel,
                "url": produto.get("link") or "",
            })

            if len(produtos) >= quantidade:
                break

        inicio += tamanho_pagina

        if len(dados) < tamanho_pagina:
            break

    return produtos
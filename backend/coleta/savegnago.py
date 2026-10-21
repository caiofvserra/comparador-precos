
import re
import unicodedata

import requests


URL_BASE = "https://www.savegnago.com.br"
URL_SESSOES = f"{URL_BASE}/api/sessions"
URL_BUSCA = (
    f"{URL_BASE}/api/catalog_system/pub/products/search"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def criar_sessao(cep="14010000"):
    """Cria uma sessão regionalizada para o CEP informado."""
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


def _normalizar(texto):
    """Remove acentos e transforma o texto em palavras normalizadas."""
    texto = unicodedata.normalize(
        "NFKD",
        str(texto or "").casefold(),
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    return re.findall(r"[a-z0-9]+", texto)


def _consultar(sessao, termo, quantidade):
    """Consulta a API. Retorna None quando a busca é bloqueada com HTTP 400."""
    resposta = sessao.get(
        URL_BUSCA,
        params={
            "ft": termo,
            "_from": 0,
            "_to": quantidade - 1,
        },
        timeout=30,
    )

    if resposta.status_code == 400:
        return None

    resposta.raise_for_status()

    dados = resposta.json()

    if not isinstance(dados, list):
        raise ValueError(
            "A API do Savegnago retornou um formato inesperado."
        )

    return dados


def _pontuar_produto(produto, palavras_busca):
    """Pontua a correspondência entre a busca e o nome do produto."""
    nome = _normalizar(produto.get("productName"))
    marca = _normalizar(produto.get("brand"))

    palavras_nome = set(nome)
    palavras_marca = set(marca)

    pontos = 0

    for palavra in palavras_busca:
        if palavra in palavras_nome:
            pontos += 3
        elif palavra in palavras_marca:
            pontos += 2

    # Dá preferência a produtos cujo nome contenha a expressão buscada.
    # Essa comparação é feita após normalizar acentos e pontuação.
    texto_nome = " ".join(nome)
    expressao = " ".join(palavras_busca)

    if expressao and expressao in texto_nome:
        pontos += 5

    return pontos


def buscar_produtos(
    termo="leite",
    quantidade=5,
    cep="14010000",
):
    """
    Consulta produtos do Savegnago sem gravar no banco.

    Quando uma busca com várias palavras retorna HTTP 400,
    tenta consultar as palavras individualmente e combina os resultados.
    """
    if not 1 <= quantidade <= 50:
        raise ValueError(
            "A quantidade deve estar entre 1 e 50."
        )

    if not str(termo).strip():
        raise ValueError("Informe um termo para a busca.")

    sessao = criar_sessao(cep)

    palavras = list(dict.fromkeys(_normalizar(termo)))

    if not palavras:
        return []

    resultados = _consultar(
        sessao,
        str(termo).strip(),
        quantidade,
    )

    if resultados is None:
        # A busca original foi bloqueada. Consultamos cada palavra.
        encontrados = {}

        for palavra in palavras:
            # Ignora artigos e preposições muito curtos para evitar
            # buscas pouco úteis, como "de" e "e".
            if len(palavra) <= 2:
                continue

            # Busca até 50 resultados por palavra para não
            # perder produtos relevantes que aparecem depois.
            produtos_palavra = _consultar(
                sessao,
                palavra,
                max(quantidade, 50),
            )

            if produtos_palavra is None:
                continue

            for produto in produtos_palavra:
                identificador = str(
                    produto.get("productId") or ""
                ).strip()

                if identificador:
                    encontrados[identificador] = produto

        # Para buscas compostas, exige que todas as palavras
        # relevantes estejam no nome ou na marca.
        palavras_relevantes = [
            palavra for palavra in palavras
            if len(palavra) > 2
        ]

        def corresponde(produto):
            nome_marca = set(
                _normalizar(produto.get("productName"))
                + _normalizar(produto.get("brand"))
            )

            return all(
                palavra in nome_marca
                for palavra in palavras_relevantes
            )

        candidatos = [
            produto
            for produto in encontrados.values()
            if corresponde(produto)
        ]

        resultados = sorted(
            candidatos,
            key=lambda produto: _pontuar_produto(
                produto,
                palavras,
            ),
            reverse=True,
        )[:quantidade]

    produtos = []

    for produto in resultados:
        itens = produto.get("items") or []
        item = itens[0] if itens else {}

        vendedores = item.get("sellers") or []

        vendedor = next(
            (
                v
                for v in vendedores
                if "SAVEGNAGO" in str(
                    v.get("sellerName") or ""
                ).upper()
            ),
            {},
        )

        oferta = vendedor.get("commertialOffer") or {}

        ean = str(item.get("ean") or "").strip()

        if ean == "0":
            ean = ""
        imagens = item.get("images") or []
        imagem_url = imagens[0].get("imageUrl") if imagens else ""
        produtos.append({
            "id_externo": str(
                produto.get("productId") or ""
            ),
            "sku": str(item.get("itemId") or ""),
            "vendedor_id": str(
                vendedor.get("sellerId") or ""
            ),
            "vendedor_nome": str(
                vendedor.get("sellerName") or ""
            ),
            "nome": produto.get("productName") or "",
            "marca": produto.get("brand") or "",
            "codigo_barras": ean,
            "preco": oferta.get("Price"),
            "disponivel": oferta.get(
                "IsAvailable",
                False,
            ),
            "url": produto.get("link") or "",
            "imagem_url": imagem_url,
        })

    return produtos

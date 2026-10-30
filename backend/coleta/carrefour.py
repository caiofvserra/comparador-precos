import json
import re
from html import unescape
from urllib.parse import quote, urljoin

import requests


URL_BASE = "https://mercado.carrefour.com.br"
USER_AGENT = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; "
    "+http://www.google.com/bot.html)"
)


def criar_sessao():
    """Cria uma sessão HTTP para consultar o site do Carrefour."""
    sessao = requests.Session()
    sessao.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    return sessao


def _buscar_valor_gtin(produto):
    """Obtém um EAN/GTIN válido dos dados estruturados do produto."""
    for campo in ("gtin", "gtin8", "gtin12", "gtin13", "gtin14"):
        valor = produto.get(campo)
        if not valor:
            continue

        codigo = re.sub(r"\D", "", str(valor))
        if len(codigo) in (8, 12, 13, 14):
            return codigo

    return ""


def _encontrar_produtos_json(dados):
    """Percorre objetos JSON-LD procurando produtos."""
    encontrados = []

    if isinstance(dados, list):
        for item in dados:
            encontrados.extend(_encontrar_produtos_json(item))

    elif isinstance(dados, dict):
        tipo = dados.get("@type", [])
        tipos = tipo if isinstance(tipo, list) else [tipo]

        if any(str(t).lower() == "product" for t in tipos):
            encontrados.append(dados)

        for chave, valor in dados.items():
            if chave in ("@context", "@type"):
                continue
            if isinstance(valor, (dict, list)):
                encontrados.extend(_encontrar_produtos_json(valor))

    return encontrados


def _extrair_produto(html, url):
    """Extrai os dados estruturados de uma página de produto."""
    scripts = re.findall(
        r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>"
        r"(.*?)</script\s*>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    candidatos = []

    for script in scripts:
        try:
            dados = json.loads(unescape(script).strip())
        except (json.JSONDecodeError, TypeError):
            continue

        candidatos.extend(_encontrar_produtos_json(dados))

    for produto in candidatos:
        ean = _buscar_valor_gtin(produto)
        nome = str(produto.get("name") or "").strip()

        if not ean or not nome:
            continue

        ofertas = produto.get("offers") or []
        if isinstance(ofertas, dict):
            ofertas = [ofertas]

        oferta = next(
            (
                item for item in ofertas
                if isinstance(item, dict)
                and item.get("price") is not None
            ),
            {},
        )

        try:
            preco = float(
                str(oferta.get("price", "")).replace(",", ".")
            )
        except (ValueError, TypeError):
            preco = None

        disponibilidade = str(
            oferta.get("availability") or ""
        ).lower()

        disponivel = (
            "instock" in disponibilidade
            and "outofstock" not in disponibilidade
        )

        marca = produto.get("brand") or ""
        if isinstance(marca, dict):
            marca = marca.get("name") or ""

        sku = str(
            produto.get("sku")
            or produto.get("productID")
            or ""
        ).strip()

        return {
            "nome": nome,
            "marca": str(marca).strip(),
            "codigo_barras": ean,
            "sku": sku,
            "preco": preco,
            "disponivel": disponivel,
            "url": url,
        }

    return None


def buscar_produtos(termo="arroz", quantidade=15):
    """
    Busca páginas do Carrefour e extrai dados dos produtos.
    Não grava nada no banco de dados.
    """
    termo = str(termo).strip()

    if not termo:
        raise ValueError("Informe um termo para a busca.")

    if not 1 <= quantidade <= 50:
        raise ValueError("A quantidade deve estar entre 1 e 50.")

    sessao = criar_sessao()
    url_busca = f"{URL_BASE}/busca/{quote(termo)}"

    resposta = sessao.get(url_busca, timeout=30)
    resposta.raise_for_status()

    links = re.findall(
        r'href="(/produto/[^"]+)"[^>]*data-testid="search-product-card"',
        resposta.text,
        flags=re.IGNORECASE,
    )

    # Remove links repetidos preservando a ordem.
    links_unicos = list(dict.fromkeys(links))[:quantidade]
    produtos = []

    for caminho in links_unicos:
        url = urljoin(URL_BASE, caminho)

        try:
            pagina = sessao.get(url, timeout=30)
            pagina.raise_for_status()
            produto = _extrair_produto(pagina.text, url)

        except requests.RequestException as erro:
            produtos.append({
                "url": url,
                "erro": str(erro),
            })
            continue

        if produto is None:
            produtos.append({
                "url": url,
                "erro": "Dados estruturados de produto não encontrados.",
            })
        else:
            produtos.append(produto)

    return produtos

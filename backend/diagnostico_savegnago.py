import requests

from coleta.savegnago import URL_SESSOES, URL_BUSCA

CEP = "14010000"
QUANTIDADE = 20

sessao = requests.Session()
sessao.headers.update({
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
})

resposta = sessao.post(
    URL_SESSOES,
    json={
        "public": {
            "country": {"value": "BRA"},
            "postalCode": {"value": CEP},
        }
    },
    timeout=30,
)

print("Sessão:", resposta.status_code)
resposta.raise_for_status()

for termo in ["leite", "integral", "leite integral"]:
    print(f"\n{'=' * 50}")
    print(f"TERMO: {termo}")

    try:
        resposta = sessao.get(
            URL_BUSCA,
            params={
                "ft": termo,
                "_from": 0,
                "_to": QUANTIDADE - 1,
            },
            timeout=30,
        )

        print("HTTP:", resposta.status_code)

        if resposta.status_code == 400:
            print("Busca bloqueada pela API.")
            continue

        resposta.raise_for_status()
        dados = resposta.json()

        print("Quantidade retornada:", len(dados))

        for produto in dados:
            nome = produto.get("productName", "")
            marca = produto.get("brand", "")
            print(f"- {nome} | Marca: {marca}")

    except (requests.RequestException, ValueError) as erro:
        print("Erro:", repr(erro))

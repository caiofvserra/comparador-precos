#!/usr/bin/env python3
"""Aciona o coletor no Render com OIDC do GitHub (sem senhas no repositório).

A Action só termina com sucesso após o Django registrar a conclusão no banco.
Nas primeiras tentativas, aceita 404/502 enquanto um deploy entra no ar.
"""

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

AUDIENCE = "comparador-precos-coleta"
BASE_URL = os.environ["COLETOR_URL"].rstrip("/")
URL_TOKEN = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
TOKEN_REQUISICAO = os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]


def obter_oidc():
    separador = "&" if "?" in URL_TOKEN else "?"
    endereco = URL_TOKEN + separador + urlencode({"audience": AUDIENCE})
    req = Request(
        endereco,
        headers={"Authorization": f"Bearer {TOKEN_REQUISICAO}"},
    )
    with urlopen(req, timeout=20) as resposta:
        token = json.load(resposta)["value"]
    return token


def requisicao(url, metodo="GET"):
    # Token atualizado a cada chamada, inclusive durante polling de execuções longas.
    token = obter_oidc()
    req = Request(
        url,
        method=metodo,
        data=b"{}" if metodo == "POST" else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urlopen(req, timeout=65) as resposta:
        return json.load(resposta)


def iniciar():
    endereco = BASE_URL + "/api/v1/interno/coleta/"
    for tentativa in range(1, 31):
        try:
            return requisicao(endereco, metodo="POST")
        except HTTPError as erro:
            if erro.code not in (404, 502, 503, 504):
                raise RuntimeError(f"Falha HTTP ao iniciar coleta: {erro.code}") from erro
            print(f"Serviço indisponível (HTTP {erro.code}); tentativa {tentativa}/30.", flush=True)
        except URLError as erro:
            print(f"Conexão ainda não pronta: {erro.reason} ({tentativa}/30).", flush=True)
        time.sleep(20)
    raise RuntimeError("O serviço não disponibilizou o endpoint em 10 minutos.")


def executar():
    # Um deploy pode interromper o subprocesso remoto. Nesse caso, após
    # o watchdog marcar a execução como erro, reinicia uma única vez.
    for reinicio in range(2):
        resposta = iniciar()
        execucao_id = resposta["id"]
        print(f"Coleta solicitada no Render. Execução nº {execucao_id}.", flush=True)
        url = BASE_URL + f"/api/v1/interno/coleta/{execucao_id}/"

        for tentativa in range(1, 151):
            time.sleep(15)
            try:
                resultado = requisicao(url)
            except (HTTPError, URLError) as erro:
                if isinstance(erro, HTTPError) and erro.code in (401, 403):
                    raise
                print(f"Consulta de andamento indisponível: {erro}.", flush=True)
                continue

            estado = resultado.get("estado")
            if estado == "concluida":
                print("Atualização confirmada no PostgreSQL:", flush=True)
                print(json.dumps(resultado, ensure_ascii=False, indent=2), flush=True)
                return
            if estado == "erro":
                detalhe = str(resultado.get("erro", ""))
                if "Coleta interrompida" in detalhe and reinicio == 0:
                    print(
                        "Processo remoto interrompido (possível deploy). "
                        "Iniciando mais uma tentativa segura.",
                        flush=True,
                    )
                    break
                raise RuntimeError("A coleta falhou no Render: " + detalhe[:400])
            if tentativa % 4 == 0:
                print(
                    f"Coleta em execução: {estado}, "
                    f"{resultado.get('novos_registros', 0)} registros até agora.",
                    flush=True,
                )
        else:
            raise RuntimeError("Tempo limite ao aguardar conclusão no Render.")

    raise RuntimeError("A coleta foi interrompida novamente após a tentativa de recuperação.")


if __name__ == "__main__":
    try:
        executar()
    except Exception as erro:
        print(f"ERRO: {erro}", file=sys.stderr, flush=True)
        sys.exit(1)

"""Endpoint autenticado pelo OIDC do GitHub Actions, sem segredo compartilhado.

Somente o workflow de coleta da branch main deste repositório pode acioná-lo.
O trabalho continua num subprocesso, porque a atualização dura mais que
o timeout de uma requisição web. O resultado fica registrado no PostgreSQL.
"""

from datetime import timedelta
import logging
import subprocess
import sys

import jwt
from jwt import PyJWKClient
from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from coleta.models import ExecucaoColeta
from precos.models import Preco

LOGGER = logging.getLogger(__name__)
GITHUB_ISSUER = "https://token.actions.githubusercontent.com"
GITHUB_AUDIENCE = "comparador-precos-coleta"
GITHUB_REPO = "caiofvserra/comparador-precos"
GITHUB_WORKFLOW_REF = (
    "caiofvserra/comparador-precos/.github/workflows/coleta-diaria.yml@refs/heads/main"
)
JWK_CLIENT = PyJWKClient(
    "https://token.actions.githubusercontent.com/.well-known/jwks",
    cache_jwk_set=True,
    lifespan=3600,
)


def autenticar_github(request):
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith("Bearer "):
        return None
    token = cabecalho.removeprefix("Bearer ").strip()
    if not token or len(token) > 10000:
        return None
    try:
        chave = JWK_CLIENT.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key=chave.key,
            algorithms=["RS256"],
            audience=GITHUB_AUDIENCE,
            issuer=GITHUB_ISSUER,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            leeway=20,
        )
    except (jwt.PyJWTError, ValueError, OSError):
        LOGGER.warning("[coleta-agendada] Rejeitado token OIDC inválido")
        return None
    if (
        claims.get("repository") != GITHUB_REPO
        or claims.get("ref") != "refs/heads/main"
        or claims.get("workflow_ref") != GITHUB_WORKFLOW_REF
        or claims.get("event_name") not in {"schedule", "workflow_dispatch", "push"}
    ):
        return None
    return claims


def resposta_negada():
    resposta = JsonResponse({"erro": "Não autorizado"}, status=403)
    resposta["Cache-Control"] = "no-store"
    return resposta


@csrf_exempt
@require_http_methods(["POST"])
def iniciar_coleta(request):
    claims = autenticar_github(request)
    if not claims:
        return resposta_negada()

    # Impede que uma nova execução simultânea sobreponha a anterior.
    limite = timezone.now() - timedelta(minutes=90)
    corrente = ExecucaoColeta.objects.filter(
        estado__in=[
            ExecucaoColeta.Estados.PENDENTE,
            ExecucaoColeta.Estados.EXECUTANDO,
        ],
        iniciada_em__gte=limite,
    ).first()
    if corrente:
        return JsonResponse(
            {"id": corrente.pk, "estado": corrente.estado, "em_andamento": True},
            status=202,
        )

    execucao = ExecucaoColeta.objects.create(
        origem=claims["event_name"],
    )
    try:
        subprocess.Popen(
            [
                sys.executable, "-u", str(settings.BASE_DIR / "manage.py"),
                "coleta_agendada", "--execucao-id", str(execucao.pk),
            ],
            cwd=str(settings.BASE_DIR),
            close_fds=True,
            start_new_session=True,
            # STDOUT e STDERR herdados do serviço: aparecem nos logs do Render.
        )
    except OSError as exc:
        LOGGER.exception("[coleta-agendada] Erro ao iniciar subprocesso")
        execucao.estado = ExecucaoColeta.Estados.ERRO
        execucao.erro = str(exc)[:1500]
        execucao.finalizada_em = timezone.now()
        execucao.save(update_fields=["estado", "erro", "finalizada_em"])
        return JsonResponse({"erro": "Falha ao iniciar coleta"}, status=500)

    resposta = JsonResponse(
        {"id": execucao.pk, "estado": execucao.estado, "em_andamento": True},
        status=202,
    )
    resposta["Cache-Control"] = "no-store"
    return resposta


@require_http_methods(["GET"])
def situacao_coleta(request, execucao_id):
    if not autenticar_github(request):
        return resposta_negada()
    execucao = ExecucaoColeta.objects.filter(pk=execucao_id).first()
    if execucao is None:
        return JsonResponse({"erro": "Execução não encontrada"}, status=404)

    registros = Preco.objects.filter(
        data_hora_coleta__gte=execucao.iniciada_em,
    )
    if execucao.finalizada_em:
        registros = registros.filter(
            data_hora_coleta__lte=execucao.finalizada_em,
        )
    detalhes = {
        linha["oferta_fonte__supermercado__nome"]: linha["total"]
        for linha in registros.values(
            "oferta_fonte__supermercado__nome"
        ).annotate(total=Count("id"))
    }
    resposta = JsonResponse({
        "id": execucao.pk,
        "estado": execucao.estado,
        "inicio": execucao.iniciada_em.isoformat(),
        "fim": execucao.finalizada_em.isoformat() if execucao.finalizada_em else None,
        "novos_registros": sum(detalhes.values()),
        "por_supermercado": detalhes,
        "erro": execucao.erro[:500],
    })
    resposta["Cache-Control"] = "no-store"
    return resposta

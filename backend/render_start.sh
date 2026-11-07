#!/usr/bin/env sh
set -e

python manage.py migrate --noinput

# Importações opcionais em série, sem bloquear a disponibilidade do site.
# O piloto multimercado é ativado somente sob BOOTSTRAP_COMPARACAO=true.
if [ "${BOOTSTRAP_SAVEGNAGO:-false}" = "true" ] || [ "${BOOTSTRAP_COMPARACAO:-false}" = "true" ]; then
  (
    if [ "${BOOTSTRAP_SAVEGNAGO:-false}" = "true" ]; then
      echo "[bootstrap] Validando catálogo inicial Savegnago."
      python -u manage.py popular_catalogo_inicial ||
        echo "[bootstrap] Falha no Savegnago; servidor continua disponível."
    fi
    if [ "${BOOTSTRAP_COMPARACAO:-false}" = "true" ]; then
      echo "[bootstrap] Iniciando piloto de comparação multirrede."
      python -u manage.py popular_comparacao_inicial ||
        echo "[bootstrap] Falha na comparação; servidor continua disponível."
    fi
  ) &
fi

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120

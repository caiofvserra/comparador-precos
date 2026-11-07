#!/usr/bin/env sh
set -e

python manage.py migrate --noinput

# Prioriza a subida do Gunicorn e o health check. A coleta começa
# somente depois de uma pequena espera, em um único subprocesso.
# A importação multirrede depende de habilitação explícita.
if [ "${BOOTSTRAP_TRIANGULACAO:-false}" = "true" ]; then
  (
    sleep 25
    echo "[triangulacao] Iniciando coleta controlada de preços nas três redes."
    python -u manage.py triangular_precos --gravar ||
      echo "[triangulacao] Coleta não concluída; site preservado."
  ) &
elif [ "${BOOTSTRAP_COMPARACAO:-false}" = "true" ]; then
  (
    sleep 25
    echo "[bootstrap] Piloto multimercado iniciado depois da subida do site."
    python -u manage.py popular_comparacao_inicial ||
      echo "[bootstrap] Coleta multirrede indisponível; site preservado."
  ) &
elif [ "${BOOTSTRAP_SAVEGNAGO:-false}" = "true" ]; then
  (
    sleep 25
    echo "[bootstrap] Catálogo inicial Savegnago iniciado após health check."
    python -u manage.py popular_catalogo_inicial ||
      echo "[bootstrap] Fonte Savegnago indisponível; site preservado."
  ) &
fi

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120

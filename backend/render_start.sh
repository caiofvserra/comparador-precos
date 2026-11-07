#!/usr/bin/env sh
set -e

python manage.py migrate --noinput

# A coleta inicial é opcional e acontece em paralelo ao servidor.
# Não criamos cron pago nem bloqueamos o health check do serviço gratuito.
if [ "${BOOTSTRAP_SAVEGNAGO:-false}" = "true" ]; then
  (
    echo "[bootstrap] Coleta inicial iniciada em segundo plano."
    python manage.py popular_catalogo_inicial ||
      echo "[bootstrap] Falha na coleta inicial; aplicação web preservada."
  ) &
fi

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120

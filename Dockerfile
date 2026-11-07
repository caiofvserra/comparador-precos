# Build do frontend Vue
FROM node:24-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# Em produção o frontend usa a API no mesmo domínio.
ENV VITE_DEMO_MODE=false
RUN npm run build


# Aplicação Django
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./frontend_dist

# Coleta os arquivos estáticos do Django Admin.
RUN DJANGO_SECRET_KEY=build-only \
    DB_NAME=build \
    DB_USER=build \
    DB_PASSWORD=build \
    python manage.py collectstatic --noinput

RUN chmod +x ./render_start.sh

EXPOSE 10000

CMD ["./render_start.sh"]

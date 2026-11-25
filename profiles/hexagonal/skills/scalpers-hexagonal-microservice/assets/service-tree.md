# Árbol objetivo del piloto

Un repo, varios servicios en carpetas, un compose raíz. El sistema llamante no vive aquí.

```
piloto/
├── compose.yaml
├── Dockerfile
├── Makefile
├── .env.example
├── contracts/
│   ├── order-request.schema.json
│   ├── order-response.schema.json
│   └── openapi.yaml
├── config/
│   ├── providers/
│   └── consumers.yaml
├── services/
│   ├── orders-api/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/orders/
│   │   └── tests/
│   ├── notification-worker/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── src/
│   └── <servicio-futuro>/
├── tests/
│   └── e2e/
├── scripts/
├── docs/
└── ops/
```

## Compose raíz

```yaml
name: platform-pilot
services:
  orders-api:
    build:
      context: .
      dockerfile: Dockerfile
      target: orders-api
    env_file: .env
    ports:
      - "8080:8080"
    volumes:
      - ./config:/app/config:ro
      - ./contracts:/app/contracts:ro
      - ./var:/app/var
  notification-worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: notification-worker
    env_file: .env
```

## Dockerfile con targets

```dockerfile
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY contracts /app/contracts
COPY config /app/config

FROM base AS orders-api
COPY services/orders-api/pyproject.toml services/orders-api/uv.lock /app/
RUN uv sync --frozen --no-dev
COPY services/orders-api/src /app/src
ENV PYTHONPATH=/app/src
EXPOSE 8080
CMD ["uv", "run", "uvicorn", "orders.api.asgi:app", "--host", "0.0.0.0", "--port", "8080"]

FROM base AS notification-worker
COPY services/notification-worker/pyproject.toml services/notification-worker/uv.lock /app/
RUN uv sync --frozen --no-dev
COPY services/notification-worker/src /app/src
ENV PYTHONPATH=/app/src
CMD ["uv", "run", "python", "-m", "notification.main"]
```

## Makefile raíz

```make
.PHONY: up down logs test e2e
up:
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f --tail=200
test:
	docker compose run --rm orders-api pytest
e2e:
	docker compose run --rm orders-api pytest tests/e2e
```

## Reglas

- `contracts/` y `config/` son compartidos; cada servicio los recibe como volumen o los copia en
  la imagen.
- Cada servicio tiene su `pyproject.toml`, sus tests y su Dockerfile target.
- Los tests E2E entre servicios viven en `tests/e2e/` del repo raíz.
- El sistema llamante (monolito, ERP, legacy) se integra por contrato y adaptador; no se añade como
  servicio de este compose ni comparte su base de datos.

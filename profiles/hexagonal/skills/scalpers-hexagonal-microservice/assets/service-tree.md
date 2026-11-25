# Árbol objetivo del piloto

Un repo, varios servicios en carpetas, un compose raíz. El módulo de Odoo no vive aquí.

```
piloto/
├── compose.yaml
├── Dockerfile
├── Makefile
├── .env.example
├── contracts/
│   ├── shipment-request.schema.json
│   ├── shipment-response.schema.json
│   └── openapi.yaml
├── config/
│   ├── carriers/
│   └── consumers.yaml
├── services/
│   ├── transport-api/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/transport/
│   │   └── tests/
│   ├── carrier-mock/
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
name: transporte-piloto
services:
  transport-api:
    build:
      context: .
      dockerfile: Dockerfile
      target: transport-api
    env_file: .env
    ports:
      - "8080:8080"
    volumes:
      - ./config:/app/config:ro
      - ./contracts:/app/contracts:ro
      - ./var:/app/var
  carrier-mock:
    build:
      context: .
      dockerfile: Dockerfile
      target: carrier-mock
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

FROM base AS transport-api
COPY services/transport-api/pyproject.toml services/transport-api/uv.lock /app/
RUN uv sync --frozen --no-dev
COPY services/transport-api/src /app/src
ENV PYTHONPATH=/app/src
EXPOSE 8080
CMD ["uv", "run", "uvicorn", "transport.api.asgi:app", "--host", "0.0.0.0", "--port", "8080"]

FROM base AS carrier-mock
COPY services/carrier-mock/pyproject.toml services/carrier-mock/uv.lock /app/
RUN uv sync --frozen --no-dev
COPY services/carrier-mock/src /app/src
ENV PYTHONPATH=/app/src
EXPOSE 8081
CMD ["uv", "run", "uvicorn", "carrier_mock.main:app", "--host", "0.0.0.0", "--port", "8081"]
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
	docker compose run --rm transport-api pytest
e2e:
	docker compose run --rm transport-api pytest tests/e2e
```

## Reglas

- `contracts/` y `config/` son compartidos; cada servicio los recibe como volumen o los copia en
  la imagen.
- Cada servicio tiene su `pyproject.toml`, sus tests y su Dockerfile target.
- Los tests E2E entre servicios viven en `tests/e2e/` del repo raíz.
- El módulo de Odoo se queda en `scalpers-v11`; no se añade a este compose salvo que el piloto
  levante un Odoo completo, y en ese caso se monta como addon, no como servicio del repo.

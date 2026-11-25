# Arquitectura hexagonal para microservicios Scalpers

Base para cualquier microservicio, independiente del dominio y del sistema que lo llame. La
regla de oro es siempre la misma: el dominio no sabe cómo se entra ni cómo se sale; los
adaptadores lo conectan.

## 1. Regla de dependencia

```
api ──► application ──► domain ◄── infrastructure
                              ▲
                       ports (Protocol)
```

- `domain/` no importa `fastapi`, `pydantic`, `requests`, `sqlite3`, `yaml` ni `infrastructure/`.
- `application/` orquesta dominio y habla con puertos; no abre conexiones ni construye clientes.
- `infrastructure/` implementa puertos; puede importar `domain` y `application`.
- `api/` traduce HTTP ↔ DTO; no contiene reglas de negocio.
- La composición (`create_app`) es el único sitio que conoce implementaciones concretas.
- Un test de arquitectura con `ast` recorre `domain/` y falla si aparece un import prohibido.

## 2. Estructura canónica de un servicio

```
services/<servicio>/
├── pyproject.toml
├── Dockerfile
├── src/<paquete>/
│   ├── domain/
│   │   ├── entities.py
│   │   ├── value_objects.py
│   │   ├── status.py
│   │   ├── errors.py
│   │   └── ports.py
│   ├── application/
│   │   ├── dto.py
│   │   ├── responses.py
│   │   └── use_cases/
│   ├── infrastructure/
│   │   ├── persistence/
│   │   ├── clients/
│   │   ├── storage/
│   │   └── config/
│   ├── api/
│   │   ├── main.py
│   │   ├── asgi.py
│   │   ├── deps.py
│   │   ├── errors.py
│   │   └── routers/
│   └── settings.py
└── tests/
    ├── unit/
    ├── contract/
    ├── api/
    └── test_architecture.py
```

En un piloto con varios microservicios, `services/` cuelga del repo único del piloto. En
plataforma, cada componente puede separarse en su repositorio.

## 3. Dominio

- Entidades y value objects inmutables (`@dataclass(frozen=True, slots=True)`) cuando representan
  valores; entidades mutables solo si el ciclo de vida lo exige.
- Dinero con `Decimal` y divisa ISO 4217 como cadena, nunca `float`.
- Unidades explícitas: moneda, tiempo, cantidad; conversiones y redondeos en el dominio.
- Estados normalizados en un `StrEnum`; los estados del proveedor se traducen en su adaptador.
- Errores de dominio con atributos útiles (`provider_code`, `external_ref`), sin HTTP ni JSON.
- Puertos como `Protocol` en `domain/ports.py`; sus tipos son de dominio, no de framework.
- Prohibido en dominio: conocer la base de datos, la capa HTTP, el sistema llamante o el
  formato de la API.

## 4. Aplicación

- DTOs Pydantic solo en el borde (`extra="forbid"`, patrones, longitudes, enums) y mapeo explícito
  a dominio. El dominio no ve el DTO.
- Un caso de uso por acción: `CreateX`, `GetX`, `CancelX`, `ListX`, `CloseX`.
- El caso de uso recibe puertos por constructor; no los busca en globales.
- Respuestas HTTP construidas en `responses.py` a partir de dominio y resultados de puerto.
- La idempotencia, la transacción y el orden de las llamadas viven en el caso de uso.

## 5. Contrato y API

- JSON Schema 2020-12 para payloads, OpenAPI 3.1 para endpoints y ejemplos versionados.
- SemVer del contrato independiente de la versión del servicio. Aditivo = menor; quitar, renombrar
  o endurecer = mayor y ventana de migración.
- Validar ejemplos contra el esquema en tests y comprobar que la copia del repo no se desvía.
- Errores `application/problem+json` (RFC 9457) con `type`, `title`, `status` y `code` estable.
- Códigos de error cerrados y documentados; un `code` nuevo es un cambio de contrato.
- Un 4xx no oculta un error de validación; un 502 no filtra el mensaje crudo del proveedor: se
  registra y se devuelve un texto genérico.
- `Idempotency-Key`, si existe, debe coincidir con el `request_id` del cuerpo.
- Autenticación por API key por consumidor, hash en configuración y permisos por recurso. 401 sin
  clave; 403 con clave sin permiso.

## 6. Idempotencia y ciclo de vida

Aplica cuando el servicio tiene efectos o llamadas salientes. Un servicio de solo lectura no
necesita `pending`, `outcome_unknown` ni claim previo.

Estados internos: `pending`, `completed`, `failed`, `outcome_unknown`.

1. Calcular el hash del cuerpo canónico (`json.dumps(..., sort_keys=True)`).
2. Buscar `(consumer_id, request_id)`:
   - `completed` y mismo hash → replay de la respuesta guardada.
   - hash distinto → 422 `idempotency_key_reused`.
   - `pending` → 409 `duplicate_request`.
   - `outcome_unknown` → 502 hasta conciliar por la referencia externa.
   - `failed` → reintento con el mismo `request_id` y el mismo cuerpo; si el cuerpo cambia, nuevo
     `request_id`.
3. Insertar la fila `pending` con restricción única `(consumer_id, request_id)` antes de llamar al
   proveedor. Capturar la violación de unicidad y releer; nunca devolver 500 por una carrera.
4. Llamar al puerto.
5. Guardar resultado, artefactos y eventos, y pasar a `completed` en la misma transacción.

Errores del proveedor:

| Caso | Estado | Respuesta | Reintento |
|---|---|---|---|
| Rechazo de validación del proveedor | `failed` | 4xx con `provider_code` | Corregir y reintentar |
| No se pudo conectar antes de enviar | `failed` | 502 | Mismo `request_id` |
| Timeout, 5xx o error de lectura tras enviar | `outcome_unknown` | 502 | No automático; conciliar |

Reglas de concurrencia:

- La unicidad se resuelve con `INSERT` + captura de `IntegrityError` + relectura.
- El reintento de `failed` es un `UPDATE ... WHERE lifecycle='failed'` y comprueba `rowcount`.
- Un índice único parcial protege `(external_ref, provider)` mientras el recurso está activo; un
  recurso cancelado libera la referencia.
- No se hacen actualizaciones ni escaneos de tabla completa en rutas de petición.

## 7. Persistencia y artefactos

- El repositorio es un puerto; SQLite para tests/local y PostgreSQL para entornos compartidos.
- Migraciones SQL versionadas, idempotentes y ejecutadas al arrancar; nunca `ALTER` manual.
- Conexiones con cierre explícito (`contextmanager`); no depender del recolector.
- Transacciones cortas; el `complete` guarda cabecera, artefactos y evento juntos.
- Reconstruir entidades desde el payload almacenado puede fallar con datos antiguos: degradar a
  una entidad mínima y registrar el aviso, no devolver 500.
- En tablas grandes, añadir columnas nullable y evitar defaults o backfills que puedan reescribir
  la tabla al migrar. Si hace falta un valor, backfill explícito y por lotes.
- Artefactos (ficheros, documentos, imágenes si aplica): escritura atómica (`tmp` + `os.replace`),
  nombre validado, ruta contenida en la raíz y sha256 verificado al servir.

## 8. Configuración y secretos

- YAML por servicio/entorno con `${VAR}` resueltas del entorno; fail-fast al arrancar nombrando la
  variable que falta.
- Credenciales solo por entorno o vault; nunca en el repositorio, en logs ni en la respuesta.
- Campos sensibles con control de acceso del sistema; el hash de una API key no es la clave.
- Consumidores con recursos permitidos y entornos donde aplican; el seed reconcilia y deshabilita
  los que desaparecen del YAML.
- Secretos en tests: fixtures locales, nunca valores reales.

## 9. Pruebas

| Nivel | Qué cubre | Herramienta |
|---|---|---|
| Dominio | reglas, unidades, redondeos, estados, errores | pytest puro |
| Casos de uso | orquestación, idempotencia, errores | pytest + fakes de puertos |
| Contrato | ejemplos y esquemas, copia sin deriva | jsonschema, openapi-spec-validator |
| Adaptadores | mapeo y respuestas grabadas | pytest + MockTransport/cassettes |
| API | códigos, auth, permisos, problem+json | TestClient |
| Arquitectura | `domain/` sin framework | test con `ast` |
| E2E | flujo completo entre servicios | script + compose o TestClient |

- Un test por regla observable; cubre salida, código y estado persistido.
- Añade concurrencia (dos POST con el mismo `request_id`), timeout tras enviar, path traversal y
  replay tras una transición de estado.
- Los tests de adaptador no llaman al proveedor real; usan respuestas grabadas.
- Cobertura: la que fije el proyecto; esta base no impone cifras.
- Evidencia: comando, salida y fichero generado; no se declara verde sin `Ran N tests` o `passed`.

## 10. Repositorio y despliegue

- **Piloto:** un repositorio con `services/<nombre>/` por microservicio, `compose.yaml` raíz,
  Dockerfile con base común y un target por servicio, `contracts/`, `config/`, `tests/e2e/`,
  `scripts/`, `docs/` y `ops/`. Un `docker compose up` levanta todo.
- **Plataforma:** se aplica la separación de la metodología (`_doc`, `_test`, `_infra`, componentes)
  cuando el servicio deja de ser piloto.
- CI: lint, format, tipos, tests, contrato y build de imagen; el despliegue sigue el GitFlow de la
  metodología cuando aplique.
- Contenedor no root, `uv sync --frozen --no-dev`, healthcheck y variables por entorno.

## 11. Observabilidad

- `/health` y `/ready`; `ready` comprueba dependencias reales.
- Logs estructurados con IDs de petición y recurso; nunca secretos ni payloads completos.
- `/metrics` o instrumentación OpenTelemetry para latencia, errores por proveedor y volumen.
- Un 502 registra la causa; el cliente recibe un mensaje genérico.

## 12. Integración con sistemas existentes

- Un sistema existente (monolito, ERP, legacy) es un **adaptador**, no el centro del servicio.
- El adaptador traduce su modelo al contrato; no comparte tablas, transacciones ni claves internas.
- La idempotencia se sostiene en el servicio: `request_id` persistido y confirmado antes de la
  llamada, aunque el sistema llamante falle o repita la petición.
- Si el sistema llamante usa aislamiento de instantánea, no actualices la misma fila en la
  transacción principal después de confirmar el `request_id` en otra transacción; escribe el
  resultado en la transacción auxiliar y expón el estado por el contrato.
- Integración gradual: feature flag por recurso/consumidor, ejecución en paralelo, comparación de
  resultados y corte por caso de uso, nunca big bang.
- El sistema existente no debe conocer detalles del microservicio; solo el contrato.

## 13. Adaptación a otros dominios

El esqueleto no es de un dominio concreto: cambia el vocabulario y conserva las reglas.

| Dominio | Entidad | Puertos | Contrato |
|---|---|---|---|
| Facturación | Invoice/Line | BillingPort, Repository, DocumentStore | invoice-request/response |
| Notificaciones | Message | SenderPort, Repository | notification-request/response |
| Catálogo | Product | SourcePort, Repository | product-sync |
| Inventario | StockItem | WarehousePort, Repository | stock-request/response |

Checklist de adaptación:

1. Define el bounded context y los casos de uso.
2. Modela entidades y value objects con unidades explícitas.
3. Declara puertos con tipos de dominio.
4. Escribe el contrato antes del adaptador.
5. Implementa idempotencia y errores con la misma tabla de tres casos.
6. Reutiliza la estructura de tests y el test de arquitectura.
7. Cambia el nombre del servicio, el paquete y el compose; no dupliques la lógica.

## 14. Anti-patrones

- `domain/` importando FastAPI, Pydantic, SQL o `requests`.
- Reglas de negocio en routers, adaptadores o en el sistema llamante.
- Contrato que se cambia sin versión ni tests.
- Llamar al proveedor antes de confirmar el `pending`.
- Reintentar un `outcome_unknown` automáticamente.
- Devolver 500 por una carrera de unicidad o por un dato viejo.
- `default` en campos nuevos de tablas grandes.
- Escaneos o actualizaciones de tabla completa en una ruta de petición.
- Credenciales en YAML, logs o commits.
- Varios repositorios para un piloto que cabe en varias carpetas.
- Acoplar la base a un dominio, a un proveedor o a un sistema llamante.

## 15. Referencias internas

- `references/architecture.md` — este documento.
- `references/metodologia-scalpers.md` — encaje con la metodología de empresa.
- `references/checklist.md` — puerta de entrega.
- `assets/service-tree.md` — árbol de servicios, compose y Dockerfile.

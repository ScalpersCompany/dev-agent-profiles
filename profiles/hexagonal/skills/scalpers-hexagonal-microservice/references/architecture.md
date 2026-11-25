# Arquitectura hexagonal para microservicios Scalpers

Base extraída del piloto de transporte y generalizada para cualquier dominio. La regla de oro es
siempre la misma: el dominio no sabe cómo se entra ni cómo se sale; los adaptadores lo conectan.

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
- Pesos en kg con `Decimal`; dimensiones en cm; conversiones y redondeos en el dominio.
- Estados normalizados en un `StrEnum`; los estados del proveedor se traducen en su adaptador.
- Errores de dominio con atributos útiles (`provider_code`, `carrier_ref`), sin HTTP ni JSON.
- Puertos como `Protocol` en `domain/ports.py`; sus tipos son de dominio, no de framework.

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
5. Guardar resultado/labels/eventos y pasar a `completed` en la misma transacción.

Errores del proveedor:

| Caso | Estado | Respuesta | Reintento |
|---|---|---|---|
| Rechazo de validación del proveedor | `failed` | 4xx con `provider_code` | Corregir y reintentar |
| No se pudo conectar antes de enviar | `failed` | 502 | Mismo `request_id` |
| Timeout, 5xx o error de lectura tras enviar | `outcome_unknown` | 502 | No automático; conciliar |

Reglas de concurrencia:

- La unicidad se resuelve con `INSERT` + captura de `IntegrityError` + relectura.
- El reintento de `failed` es un `UPDATE ... WHERE lifecycle='failed'` y comprueba `rowcount`.
- Un índice único parcial protege `(external_ref, carrier)` mientras la expedición está activa;
  una cancelada libera la referencia.
- No se hacen `UPDATE` masivos ni `search([])` en rutas de petición.

## 7. Persistencia

- El repositorio es un puerto; SQLite para tests/local y PostgreSQL para entornos compartidos.
- Migraciones SQL versionadas, idempotentes y ejecutadas al arrancar; nunca `ALTER` manual.
- Conexiones con cierre explícito (`contextmanager`); no depender del recolector.
- Transacciones cortas; el `complete` guarda cabecera, artefactos y evento juntos.
- Reconstruir entidades desde el payload almacenado puede fallar con datos antiguos: degradar a
  una entidad mínima y registrar el aviso, no devolver 500.
- En tablas enormes, añadir columnas nullable y sin `default`; un `default` dispara un `UPDATE` de
  toda la tabla al instalar (ver lección de `stock.picking` con 45 M de filas).
- Artefactos (etiquetas, PDFs): escritura atómica (`tmp` + `os.replace`), nombre validado, ruta
  contenida en la raíz y sha256 verificado al servir.

## 8. Configuración y secretos

- YAML por servicio/entorno con `${VAR}` resueltas del entorno; fail-fast al arrancar nombrando la
  variable que falta.
- Credenciales solo por entorno o vault; nunca en el repositorio, en logs ni en la respuesta.
- Campos sensibles con grupo de sistema y ACL; el hash de una API key no es la clave.
- Consumidores con transportistas/recursos permitidos y entornos donde aplican; el seed reconcilia
  y deshabilita los que desaparecen del YAML.
- Secretos en tests: fixtures locales, nunca valores reales.

## 9. Pruebas

| Nivel | Qué cubre | Herramienta |
|---|---|---|
| Dominio | reglas, pesos, redondeos, estados, errores | pytest puro |
| Casos de uso | orquestación, idempotencia, errores | pytest + fakes de puertos |
| Contrato | ejemplos y esquemas, copia sin deriva | jsonschema, openapi-spec-validator |
| Adaptadores | mapeo y respuestas grabadas | pytest + MockTransport/cassettes |
| API | códigos, auth, permisos, problem+json | TestClient |
| Arquitectura | `domain/` sin framework | test con `ast` |
| E2E | flujo completo entre servicios | script + compose o TestClient |

- Un test por regla observable; cubre salida, código y estado persistido.
- Añade concurrencia (dos POST con el mismo `request_id`), timeout tras enviar, path traversal y
  replay tras cancelar.
- Los tests de adaptador no llaman al proveedor real; usan respuestas grabadas.
- Cobertura mínima 85 %; el dominio por encima del 90 %.
- Evidencia: comando, salida y fichero generado; no se declara verde sin `Ran N tests` o `passed`.

## 10. Repositorio y despliegue

- **Piloto:** un repositorio con `services/<nombre>/` por microservicio, `compose.yaml` raíz,
  Dockerfile con base común y un target por servicio, `contracts/`, `config/`, `tests/e2e/`,
  `scripts/`, `docs/` y `ops/`. Un `docker compose up` levanta todo.
- **Plataforma:** se aplica la separación de la metodología (`_doc`, `_test`, `_infra`, componentes)
  cuando el servicio deja de ser piloto.
- El módulo puente de Odoo es un módulo Odoo en `scalpers-v11`, con su rama y su pipeline; no es
  una carpeta de servicio ni se mezcla con el repo del piloto.
- CI: lint, format, tipos, tests, contrato y build de imagen; el despliegue sigue el GitFlow de la
  metodología cuando aplique.
- Contenedor no root, `uv sync --frozen --no-dev`, healthcheck y variables por entorno.

## 11. Observabilidad

- `/health` y `/ready`; `ready` comprueba dependencias reales.
- Logs estructurados con IDs de petición/expedición; nunca secretos ni payloads completos.
- `/metrics` o instrumentación OpenTelemetry para latencia, errores por proveedor y volumen.
- Un 502 registra la causa; el cliente recibe un mensaje genérico.

## 12. Puente Odoo

- Módulo separado en `scalpers-v11/addons`, con `__manifest__`, README, CHANGELOG, icono y tests.
- `request_id` determinista `uuid5(nombre + intento)` **confirmado en un cursor independiente**
  antes de la llamada HTTP.
- Odoo usa `REPEATABLE READ`: la transacción principal no ve lo confirmado por el cursor auxiliar y
  un `UPDATE` posterior de la misma fila puede fallar. Tras el commit auxiliar, escribe el
  resultado también en cursor auxiliar y no actualices esa fila en la transacción principal.
- El contador de intentos solo avanza tras rechazo confirmado o cancelación.
- `outcome_unknown` bloquea la regeneración hasta conciliar por `external_ref`.
- En tablas grandes no pongas `default` en campos nuevos; el `_init_column` de Odoo hace un
  `UPDATE` de toda la tabla.
- Antes de añadir una vista hija de `stock.picking`, comprueba que las vistas existentes no
  referencien campos inexistentes; una vista huérfana de otro módulo bloquea tu instalación.
- Campos nuevos con `help`, `_description` y ACL cuando corresponda; el módulo no conoce
  transportistas concretos: el código del carrier es configuración.

## 13. Adaptación a otros dominios

El esqueleto no es de transporte: cambia el vocabulario y conserva las reglas.

| Dominio | Entidad | Puertos | Contrato |
|---|---|---|---|
| Transporte | Shipment/Package | CarrierPort, Repository, LabelStore | shipment-request/response |
| Facturación | Invoice/Line | BillingPort, Repository, PdfStore | invoice-request/response |
| Notificaciones | Message | SenderPort, Repository | notification-request/response |
| Catálogo | Product | SourcePort, Repository | product-sync |

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
- Reglas de negocio en routers, adaptadores o vistas de Odoo.
- Contrato que se cambia sin versión ni tests.
- Llamar al proveedor antes de confirmar el `pending`.
- Reintentar un `outcome_unknown` automáticamente.
- Devolver 500 por una carrera de unicidad o por un dato viejo.
- `default` en campos nuevos de tablas grandes.
- `search([])` o `UPDATE` sin `WHERE id` en una ruta de petición.
- Credenciales en YAML, logs o commits.
- Cuatro repositorios para un piloto que cabe en cuatro carpetas.
- Odoo y microservicios mezclados en el mismo repo o en la misma transacción.

## 15. Referencias internas

- `transport-service/src/transport/domain` — ejemplo de dominio puro.
- `transport-service/src/transport/application/use_cases` — idempotencia y errores.
- `transport-service/src/transport/infrastructure` — adaptadores, SQLite, etiquetas y config.
- `transport-service/tests/test_architecture.py` — regla de dependencia.
- `transport-service/docs/PLAN-DESARROLLO-piloto.md` — decisiones del piloto.
- `scalpers-v11/addons/scalpers_delivery_carrier_service` — puente Odoo y cursor independiente.

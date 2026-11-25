# Changelog

## [1.3.0] - 2026-11-25

### Añadido

- E2E completo en las reglas GGA del microservicio: `E2E_CMD` sobre API y compose, con
  comando, SHA, informe y artefactos en `evidence/<run-id>/e2e/`.
- `E2E_CMD`, `E2E_BASE_URL` y `E2E_HEALTH_PATH` en el ejemplo de verify.

## [1.2.0] - 2026-11-25

### Añadido

- `gga/REVIEW-RULES.md`: reglas de revisión del microservicio que se añaden al núcleo
  agnóstico: pureza del dominio, contrato primero, idempotencia y resultados del proveedor,
  `problem+json`, persistencia, pruebas, Docker y evidencia.
- El perfil declara su contrato GGA; no hereda las reglas de Odoo ni de PHP.

## [1.1.0] - 2026-11-25

### Cambiado

- Perfil y skill desacoplados de reglas de producto y de un sistema concreto: la base sirve para cualquier dominio y
  cualquier sistema llamante.
- La integración con sistemas existentes se describe como adaptador/módulo separado, sin nombres
  ni tablas de un producto concreto.
- Regla de tablas grandes generalizada: defaults y backfills que puedan reescribir la tabla se validan con el motor; columnas nullable y backfill explícito.
- Árbol de ejemplo, contratos y compose con nombres genéricos (`orders-api`, `notification-worker`).
- Guard con denylist de stdlib con I/O, allowlist del dominio propio, detección de `open()` (también con alias de `builtins`), lectura del índice en `--staged`, `--files` exige `--staged`, detección de `builtins.print` y fallo explícito si no encuentra ningún `domain/`; 50 tests.
- El guard resuelve imports relativos por paquete actual y rechaza imports absolutos del propio paquete fuera de `domain/` (`svc.config`, `svc.application`).
- CI ejecuta los tests, la sintaxis de shell y la compilación del linter del perfil.

## [1.0.0] - 2026-11-25

### Añadido

- Perfil `hexagonal` para microservicios Scalpers: contrato, puertos y adaptadores,
  idempotencia, persistencia, pruebas y despliegue.
- Guard de arquitectura: prohíbe framework, HTTP, SQL, YAML e infraestructura en `domain/`,
  y `print()` en código de servicio.
- Skill `scalpers-hexagonal-microservice` con arquitectura, metodología Scalpers, checklist y
  árbol de servicios.
- Ejemplo de verify, 4 tests del guard y documentación del perfil.

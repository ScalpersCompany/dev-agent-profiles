# Changelog

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

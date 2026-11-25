# Checklist de entrega y revisión

## Antes de escribir

- [ ] Bounded context identificado y separado de otros servicios.
- [ ] Casos de uso enumerados (crear, consultar, cancelar, listar, cerrar...).
- [ ] Contrato y ejemplos definidos o cambio de contrato justificado.
- [ ] Puertos necesarios identificados; ningún tipo de framework en ellos.
- [ ] Riesgo evaluado: datos, seguridad, contratos, concurrencia, entrega o tests.
- [ ] Layout decidido: piloto en un repo con `services/<nombre>/`; plataforma separada.
- [ ] El servicio no contiene reglas de un dominio, producto o sistema llamante concreto.

## Dominio

- [ ] `domain/` solo importa biblioteca estándar sin I/O ni concurrencia (lista en el README del perfil) y módulos de dominio.
- [ ] Entidades y value objects con unidades explícitas (moneda, tiempo, cantidad).
- [ ] Si hay importes, dinero con `Decimal`, no `float`.
- [ ] Estados normalizados y traducción del proveedor en su adaptador.
- [ ] Errores de dominio sin HTTP, sin JSON y con datos útiles.
- [ ] `domain/ports.py` solo usa tipos de dominio.

## Aplicación e idempotencia

- [ ] DTO estricto (`extra="forbid"`) y mapeo explícito a dominio.
- [ ] Un caso de uso por acción; puertos por constructor.

Si el servicio tiene efectos o llamadas salientes:

- [ ] `(consumer, request_id)` con hash canónico y `pending` persistido antes de la llamada.
- [ ] Replay de `completed`; 409 en `pending`; 422 si cambia el cuerpo.
- [ ] `failed` reintenta con el mismo `request_id`; `outcome_unknown` no se reintenta.
- [ ] Carreras de unicidad capturadas y traducidas a replay/409, nunca a 500.
- [ ] Reintento de `failed` con `UPDATE ... WHERE lifecycle='failed'`.

## Límite y contrato

- [ ] JSON Schema/OpenAPI validados y copiados sin deriva.
- [ ] Errores con `code` estable y sin detalles crudos del proveedor.
- [ ] Si el límite es HTTP: 4xx de validación, 401 sin clave, 403 sin permiso, 404, 409 y 502 según tabla; `Idempotency-Key` coherente con `request_id` si se acepta.
- [ ] OpenAPI declara todos los endpoints que existen y ninguno que no exista, si aplica.

## Persistencia y artefactos

Si el servicio almacena estado:

- [ ] Migraciones SQL versionadas e idempotentes.
- [ ] Conexiones cerradas explícitamente.
- [ ] Restricciones únicas que protegen la idempotencia y la referencia activa.
- [ ] Sin defaults/backfills que puedan reescribir tablas grandes; nullable o backfill explícito.
- [ ] Sin escaneos ni actualizaciones de tabla completa en rutas de petición.
- [ ] Artefactos con escritura atómica, nombre validado, ruta contenida y sha256.

## Configuración y secretos

- [ ] `${VAR}` resueltas del entorno y fail-fast al arrancar.
- [ ] Credenciales fuera del repo, de logs y de respuestas.
- [ ] Si hay consumidores con permisos: recursos y entornos declarados; el seed reconcilia y deshabilita retirados.
- [ ] Campos sensibles con control de acceso del sistema.

## Pruebas

- [ ] Test de arquitectura de `domain/`.
- [ ] Unitarios de dominio y casos de uso con fakes.
- [ ] Contrato: ejemplos y esquemas; copia byte a byte.
- [ ] Adaptadores con respuestas grabadas, sin red.
- [ ] API: auth, permisos y errores; si hay efectos, replay y cancelación.
- [ ] E2E del flujo completo; evidencia de comando y salida.
- [ ] Cobertura: la que fije el proyecto.
- [ ] Si el servicio tiene efectos o llamadas salientes: concurrencia con el mismo `request_id`, timeout tras enviar y replay tras una transición.
- [ ] Si genera artefactos: path traversal y nombres duplicados.
- [ ] Si es de solo lectura: no exige `pending` ni `outcome_unknown`; contrato y tests sí.

## Integración con sistemas existentes

- [ ] El adaptador del sistema existente está separado del dominio y no comparte tablas ni
  transacciones con el servicio.
- [ ] Si hay integración o efectos: `request_id` persistido y confirmado antes de la llamada, aunque el sistema llamante falle.
- [ ] Integración gradual con feature flag y comparación de resultados, si aplica.
- [ ] El sistema existente solo conoce el contrato; no detalles internos del servicio.
- [ ] Sin reglas de un dominio, producto o sistema concreto en la base del servicio.

## Entrega

- [ ] `CHANGELOG.md` y README actualizados en el mismo commit.
- [ ] Se cumplen la norma de empresa y su checklist de entrega (`~/.agents/AGENTS.md`): commits,
  evidencia, producción y cambio destructivo.
- [ ] Riesgo declarado según el flujo de trabajo.
- [ ] `git status` limpio y rama/MR correctos.

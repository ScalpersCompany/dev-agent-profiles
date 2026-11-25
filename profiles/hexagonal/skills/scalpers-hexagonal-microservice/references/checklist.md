# Checklist de entrega y revisión

## Antes de escribir

- [ ] Bounded context identificado y separado de otros servicios.
- [ ] Casos de uso enumerados (crear, consultar, cancelar, listar, cerrar...).
- [ ] Contrato y ejemplos definidos o cambio de contrato justificado.
- [ ] Puertos necesarios identificados; ningún tipo de framework en ellos.
- [ ] Riesgo evaluado: datos, seguridad, contratos, concurrencia, entrega o tests.
- [ ] Layout decidido: piloto en un repo con `services/<nombre>/`; plataforma separada.

## Dominio

- [ ] `domain/` solo importa biblioteca estándar y módulos de dominio.
- [ ] Entidades y value objects con unidades explícitas (kg, cm, EUR, UTC).
- [ ] Dinero con `Decimal`, no `float`.
- [ ] Estados normalizados y traducción del proveedor en su adaptador.
- [ ] Errores de dominio sin HTTP, sin JSON y con datos útiles.
- [ ] `domain/ports.py` solo usa tipos de dominio.

## Aplicación e idempotencia

- [ ] DTO estricto (`extra="forbid"`) y mapeo explícito a dominio.
- [ ] Un caso de uso por acción; puertos por constructor.
- [ ] `(consumer, request_id)` con hash canónico y `pending` persistido antes de la llamada.
- [ ] Replay de `completed`; 409 en `pending`; 422 si cambia el cuerpo.
- [ ] `failed` reintenta con el mismo `request_id`; `outcome_unknown` no se reintenta.
- [ ] Carreras de unicidad capturadas y traducidas a replay/409, nunca a 500.
- [ ] Reintento de `failed` con `UPDATE ... WHERE lifecycle='failed'`.

## API y contrato

- [ ] JSON Schema/OpenAPI validados y copiados sin deriva.
- [ ] Errores `problem+json` con `code` estable.
- [ ] 4xx de validación, 401 sin clave, 403 sin permiso, 404, 409 y 502 según tabla.
- [ ] 502 sin detalles crudos del proveedor; causa en logs.
- [ ] `Idempotency-Key` coherente con `request_id` si se acepta.
- [ ] OpenAPI declara todos los endpoints que existen y ninguno que no exista.

## Persistencia y artefactos

- [ ] Migraciones SQL versionadas e idempotentes.
- [ ] Conexiones cerradas explícitamente.
- [ ] Restricciones únicas que protegen la idempotencia y la referencia activa.
- [ ] Sin `default` en campos nuevos de tablas grandes.
- [ ] Sin `search([])` ni `UPDATE` masivo en rutas de petición.
- [ ] Artefactos con escritura atómica, nombre validado, ruta contenida y sha256.

## Configuración y secretos

- [ ] `${VAR}` resueltas del entorno y fail-fast al arrancar.
- [ ] Credenciales fuera del repo, de logs y de respuestas.
- [ ] Consumidores con permisos y entornos; seed reconcilia y deshabilita retirados.
- [ ] Campos sensibles con grupo de sistema y ACL.

## Pruebas

- [ ] Test de arquitectura de `domain/`.
- [ ] Unitarios de dominio y casos de uso con fakes.
- [ ] Contrato: ejemplos y esquemas; copia byte a byte.
- [ ] Adaptadores con respuestas grabadas, sin red.
- [ ] API: auth, permisos, errores, replay, cancelación.
- [ ] Concurrencia: dos POST con el mismo `request_id`.
- [ ] Timeout tras enviar y fallo de guardado posterior.
- [ ] Path traversal y nombres duplicados.
- [ ] E2E del flujo completo; evidencia de comando y salida.
- [ ] Cobertura ≥85 % y dominio ≥90 %.

## Puente Odoo

- [ ] Módulo separado en `scalpers-v11`, con README, CHANGELOG e icono.
- [ ] `request_id` determinista confirmado en cursor independiente antes del HTTP.
- [ ] Resultado escrito también en cursor auxiliar; no se actualiza la misma fila en la
  transacción principal.
- [ ] `service_attempt` solo avanza tras rechazo o cancelación.
- [ ] `outcome_unknown` bloquea la regeneración.
- [ ] Campos nuevos con `help`; sin `default` en tablas grandes.
- [ ] Vistas existentes sin referencias a campos inexistentes.
- [ ] Tests de mapeo y de idempotencia; instalación en base desechable.
- [ ] El módulo no conoce transportistas concretos.

## Entrega

- [ ] `CHANGELOG.md` actualizado en el mismo commit.
- [ ] README con caso de uso, configuración y pruebas.
- [ ] Riesgo declarado (`Risk: item N` o `Risk: none`).
- [ ] Commits convencionales, firmados y sin atribución a IA.
- [ ] `git status` limpio y rama/MR correctos.
- [ ] Producción no tocada sin autorización explícita.

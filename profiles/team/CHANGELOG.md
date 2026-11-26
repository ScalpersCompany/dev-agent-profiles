# Changelog

## [0.1.1] - 2026-11-26

### Corregido

- La comprobación del task file acepta las tablas Markdown y las filas de andamiaje sin spec
  (`—`), y solo exige referencia `S#` a las filas de tarea (`T<n>`); antes rechazaba ficheros
  reales por líneas ajenas a la lista de tareas.
- La sección de tareas termina en cualquier encabezado de nivel 2, no solo en los tres del
  formato, para que `## Evidencia` y `## Hallazgos` no se analicen como tareas.

## [0.1.0] - 2026-11-26

### Añadido

- Perfil `team`: contrato de roles para trabajo repartido entre varios agentes sobre un mismo
  repositorio, con cuatro roles (`plan`, `dev`, `review`, `verify`) más el juez de evals del kit.
- `roles.json` y `roles.schema.json`: contrato ejecutable con superficie de escritura, lectura,
  criterio de salida por comando, rol de solo lectura y dueño del árbol por rol.
- `roles.md`: el mismo contrato para una persona, con el formato de traspaso por referencia
  (`odd/tasks/<feature>.md`, tarea y `S#`).
- `gga/REVIEW-RULES.md`: reglas bloqueantes de coordinación (traspaso sin referencia, escritura
  fuera de superficie, revisión o verificación que modifican el árbol, evidencia ausente o
  parcial, juez que se puntúa a sí mismo).
- `AGENTS.fragment.md`: reglas del perfil que se añaden al `AGENTS.md` del repositorio.
- `profile.schema.json`, `profile.env` y `README.md` del perfil.

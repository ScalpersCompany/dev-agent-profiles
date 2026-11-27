# Changelog

## [1.0.0] - 2026-11-27

### Cambiado

- El perfil `team` pasa a ser el flujo `flows/team`: `flow.json` con `entrypoint`, contrato
  de roles y etapas; ya no se activa con `DEV_AGENT_PROFILE`.
- El runner y `team_lint.py` se ejecutan desde `dev-agent flow run team` o desde la ruta del
  flujo en `dev-agent-profiles/flows/team`; las instalaciones antiguas conservan su copia.
- El guard de perfil `guard/team.sh` se retira; el contrato se valida dentro del flujo y el
  perfil base aporta guard y verify.


## [0.1.3] - 2026-11-26

### Añadido

- `bin/team-run.sh`: ejecuta `plan`, `dev`, `review` y `verify` en orden fijo y para en la
  primera etapa cuya puerta falle. Cada etapa lanza el perfil con `chat -q <consulta> -Q --in
  <repo> --max-turns N` bajo `timeout`, y la puerta la decide el script: fichero de tareas más
  `team_lint --task` en `plan`, el runner del repositorio en `dev` (`make check`, o `VERIFY_CMD`
  / `TEST_CMD` de `.dev-agent/verify.env`), un veredicto con `STATUS: PASSED` en `review` y
  `team_lint --evidence` sobre `evidence/<run-id>` en `verify`. Códigos de salida propios por
  etapa, registro por etapa y resumen final con etapa, resultado, puerta y evidencia.
- `bin/stub-cli.sh`: CLI falso para los tests y para ensayar la cadena sin llamar al modelo.
- `--from`, `--dry-run` y `--stub-cli` en el runner; `--dry-run` imprime comandos, consultas y
  puertas sin ejecutar ni escribir nada.
- `profile.json` declara `runner`, y `team_lint.py` falla el contrato si el fichero declarado no
  existe o no es ejecutable (`profile.schema.json` y `profile.env` alineados).
- Tests del runner: orden de etapas, parada en el primer rojo, puerta que rechaza pese a que el
  CLI responda 0, `--from`, timeout, runner desde `verify.env`, códigos de uso y `--dry-run`
  sin efectos.

## [0.1.2] - 2026-11-26

### Cambiado

- `roles.md` y `README.md` dejan de presentar Hermes como el mapeo de referencia: el contrato
  nombra roles, no productos, y las definiciones por agente se generan del mismo `roles.json`
  con `dev-agent roles <claude|opencode>` (un perfil de Hermes por rol se crea del mismo fichero).

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

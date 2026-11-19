---
title: "Plan Scalpers: el método de Lauren Tan en tu repo"
date: 2026-11-17
tags: [scalpers, agentes, skills, evals, opencode, guardarrailes]
status: propuesta
---

# Plan Scalpers: el método de Lauren Tan en tu repo

> Caso de uso, no el destino principal. El kit vive en la base de desarrollo; este documento muestra cómo replicarlo en un repo de empresa. La skill genérica del kit es `dev-verify`.

## Qué es y qué no

Es el método de la charla (verificación ejecutable, skills construidas desde fallos, evals y guardarraíles deterministas) aplicado a tu trabajo real en Scalpers con OpenCode, en un PC independiente. No es un trasplante de EVA ni de Hermes: aquí no hay Multica, no hay evidence gate de servidor y no hay acceso a producción. Todo vive en el repo y en esa máquina.

La diferencia con el plan general: en EVA tienes la fábrica; aquí tienes que construir el mínimo que te permita confiar en el agente en **un repo ajeno**, sin romper nada y sin depender de tu infraestructura de casa.

## Supuestos, y cómo se confirman

| Supuesto | Cómo se confirma en la fase 0 |
|---|---|
| Repo con Python y Odoo, más algo de web | `scripts/scan_env.sh` y `__manifest__.py` |
| Tests ejecutables con `--test-tags` | `docs/agent-quality/ENVIRONMENT.md` |
| Base de datos desechable | `createdb` y `TEST_CMD` |
| CI existe o se puede añadir | `.github/workflows`, `.gitlab-ci.yml` |
| Modelo aprobado por la empresa | pregunta a tu responsable, no lo asumas |
| Sin acceso a producción | se escribe en `ENVIRONMENT.md` y se prohíbe en `AGENTS.md` |

Si un supuesto falla, la fase que depende de él se para. No se rellena con una suposición.

## Los tres bucles

1. **Bucle interior: verificación.** El agente ejecuta `verify/run.sh`, lee la evidencia, arregla el primer fallo y repite. Sin artefacto no hay "hecho".
2. **Bucle de entrenamiento: evals.** Rúbrica, K ejecuciones en directorios neutros, juez de otro modelo, nota. Si baja, se cambia la skill y se repite. Esto es lo que aquí llamas entrenamiento: no es un curso, es el examen de la skill.
3. **Bucle exterior: señales.** Tickets, CI roto y avisos entran en una cola única. Un coordinador agrupa y reparte con límite de trabajo en curso. Nada de un agente por señal.

## Fase 0. Reconocimiento (día 1)

| ID | Tarea | Artefacto | Criterio |
|---|---|---|---|
| S0.1 | Escanear el repo | `docs/agent-quality/ENVIRONMENT.md` | Stack, tests, lint, CI y variables detectadas |
| S0.2 | Probar el arranque y los tests en limpio | `verify/config.env` | `TEST_CMD` y `SMOKE_CMD` reales, exit 0 |
| S0.3 | Medir el historial | `BASELINE.md` | Commits, reverts, hotfixes de las últimas 4 semanas |
| S0.4 | Confirmar el proveedor de modelo | `evals/rubric.json` | Proveedor aprobado, nunca tu clave personal |

Si no hay historial o CI, se escribe "no hay" y se sigue. Lo que no se hace es inventar una línea base.

## Fase 1. Verificación ejecutable (días 2 a 4)

| ID | Tarea | Artefacto | Criterio |
|---|---|---|---|
| S1.1 | `verify/run.sh` adaptado | `verify/config.env` | Arranca, comprueba salud, corre tests, deja `evidence/<run-id>/` |
| S1.2 | Feature map de tu área | `docs/FEATURE_MAP.md` | Cada funcionalidad con directorio, entrada y cómo llegar |
| S1.3 | Skill `dev-verify` | `.opencode/skills/dev-verify/` | El agente la usa y cita la evidencia |
| S1.4 | Un bug real reproducido | `evidence/` | El agente lo reproduce sin que le digas dónde pinchar |

En Odoo, el `TEST_CMD` típico es `odoo-bin -d <db> --test-tags /<modulo> -u <modulo> --stop-after-init`, contra una base desechable. Si el repo usa Docker, el comando va dentro del contenedor y se documenta.

## Fase 2. Skills (semana 1 a 2)

Seis skills, no cien. Cada una nace de un fallo observado, no de una lista de deseos.

| Skill | Cuándo se usa | Qué produce |
|---|---|---|
| `dev-verify` | después de cualquier cambio | evidencia y veredicto |
| `odoo-safe-change` | al tocar Python, XML, CSV o PO de Odoo | cambio seguro con tests y vistas cargadas |
| `repro-first` | al arreglar un ticket | test que falla antes y pasa después |
| `review-diff` | antes de pedir revisión | `STATUS: PASSED/FAILED` con hallazgos |
| `correct` | cuando repites la misma corrección | lint, test o CI, no otra regla en prosa |
| `query-readonly` | cuando la respuesta necesita datos | consulta y resultado en evidencia |

Regla de construcción: cada vez que el agente falle de una forma nueva, se mira la traza, se escribe la skill y se vuelve a probar. No se escribe la skill antes de ver el fallo.

## Fase 3. Guardarraíles deterministas (semana 2)

| ID | Tarea | Artefacto | Criterio |
|---|---|---|---|
| S3.1 | Lint y formato | `ruff`, `black`, `eslint` | `guard.sh` en verde en un checkout limpio |
| S3.2 | Tipos | `mypy` o `pyright`, `tsc --noEmit` | Sin errores nuevos |
| S3.3 | Reglas Odoo | `guard/odoo_lint.py` | `sudo()`, `cr.commit()`, SQL de escritura y `print()` bloqueados |
| S3.4 | Secretos | `gitleaks` | Cero hallazgos en staged |
| S3.5 | Pre-commit y CI | `.pre-commit-config.yaml` o hook | El guard corre antes de cada commit |
| S3.6 | Tabla regla a mecanismo | `docs/agent-quality/RULES.md` | Cada fila con su test |

El mensaje del lint es parte del producto: tiene que decir la causa raíz y el arreglo. Un "no permitido" a secas hace que el agente pruebe otra cosa en vez de arreglarla.

## Fase 4. Entrenamiento de skills (semana 3 a 4)

| ID | Tarea | Artefacto | Criterio |
|---|---|---|---|
| S4.1 | Rúbrica de `dev-verify` | `evals/rubric.json` | Cuatro criterios observables con peso |
| S4.2 | Tres casos | `evals/cases/` | Limpio, test roto, entorno equivocado |
| S4.3 | Primera corrida | `evals/runs/` | K=3, juez de otro modelo, `score.json` |
| S4.4 | Bucle | `evals/loop.sh` | Sube hasta el umbral o para en 3 vueltas |
| S4.5 | Segunda skill | `odoo-safe-change` | Dos casos: campo nuevo y regla de acceso |
| S4.6 | Tercera skill | `repro-first` | Dos casos: ticket claro y ticket vago |

Cómo se lee el resultado: no mires solo la media. Mira la dispersión. Una skill con media 9 y una corrida de 4 es una skill inestable. Una skill que baja 0,5 puntos respecto a la versión anterior es una regresión, aunque siga por encima del umbral.

Detalles que copiar de Lauren y que el kit ya implementa:

- Directorios con nombres neutros (`a`, `b`, `c`) para que el agente no sepa que le examinan.
- Juez de otro modelo, para que el que ejecuta no se puntúe a sí mismo.
- Rúbrica con criterios observables, no "calidad general".
- Coste y tokens por corrida en `score.json`, para saber cuánto cuesta entrenar.

## Fase 5. Bucle exterior (semana 5)

| ID | Tarea | Artefacto | Criterio |
|---|---|---|---|
| S5.1 | Cola única | `signals.db` (SQLite) | `source`, `dedupe_key`, `severity`, `status` |
| S5.2 | Ingesta | `scripts/signals.py` | Tickets y CI roto con dedupe |
| S5.3 | Coordinador | comando `/triage` | Agrupa y reparte con WIP 3 |
| S5.4 | Búfer de patrones | `docs/agent-quality/PATTERNS.md` | Revisión cada dos días, no arreglo por síntoma |

Esta fase puede esperar. Sin las tres primeras, automatizar el exterior solo acelera el ruido.

## Fase 6. Autonomía (semana 6 en adelante)

| Nivel | Qué puede hacer el agente | Promoción |
|---|---|---|
| L0 | Nada; el humano hace | - |
| L1 | Propone y el humano verifica cada paso | - |
| L2 | Verifica con `verify/run.sh` y el humano muestrea | 10 cambios verdes |
| L3 | Mergea cambios reversibles con el gate verde | 30 verdes, 0 reverts, 2 semanas |

En Scalpers, L3 significa **rama de feature**, nunca `main`, nunca producción, nunca migraciones, nunca secretos ni datos de cliente. Un revert baja un nivel automáticamente.

## El kit, archivo por archivo

| Archivo | Para qué |
|---|---|
| `AGENTS.md` | las diez reglas que el agente lee primero |
| `.opencode/skills/*` | las seis skills |
| `.opencode/commands/*` | `/verify`, `/guard`, `/repro`, `/correct`, `/eval` |
| `.opencode/agent/judge.md` | juez read-only con contrato JSON |
| `verify/run.sh` + `config.env.example` | arranque, salud, tests y evidencia |
| `guard/guard.sh` | lint, tipos, secretos y Odoo |
| `guard/odoo_lint.py` | `sudo`, `cr.commit`, SQL de escritura, `print` |
| `evals/harness.py` | K corridas en sandbox aislado, juez, nota, coste y artefactos |
| `evals/loop.sh` | subida hasta umbral |
| `scripts/scan_env.sh` | reconocimiento del repo |

Probado en local (Linux, 18-11): `bash -n` en los cuatro scripts, `py_compile` en los dos Python, el linter detecta las cuatro violaciones de prueba, `verify/run.sh` devuelve 2 sin configuración y 0 con un `TEST_CMD` de prueba (`true`), no con un test real, y el harness corre en seco con K=3 y escribe `score.json` en un sandbox aislado. El test real es la fase 0.

## Primeros 14 días

| Día | Qué haces | Qué ves |
|---|---|---|
| 1 | `scan_env.sh`, completar `ENVIRONMENT.md`, `verify/config.env` | El repo entendido por escrito |
| 2 | `verify/run.sh` en limpio | Evidencia real |
| 3 | Feature map de tu área | Mapa revisable |
| 4 | Un bug con `repro-first` | Test que falla y luego pasa |
| 5 | `guard.sh` y pre-commit | Guard en verde |
| 6 | Primer `/correct` con comentarios de revisión | Dos reglas convertidas en lint |
| 7 | Revisión de la semana | Qué funcionó y qué no |
| 8-10 | Rúbrica y tres casos de `dev-verify` | Primera nota |
| 11-12 | `odoo-safe-change` y sus dos casos | Segunda nota |
| 13 | `loop.sh` sobre la skill más floja | Curva de mejora |
| 14 | Informe de dos semanas | Números, no impresiones |

## KPIs

- Revert rate: reverts / cambios mergeados. Objetivo por debajo del 1%.
- Defectos escapados por release.
- Tiempo a merge.
- Porcentaje de tokens en verificación: debe ser la línea más grande.
- Reglas en prosa sin mecanismo: objetivo cero.

## Qué no hacer en Scalpers

1. **No instalar `rsc-harness` en el repo de trabajo.** Escribe `01-TOOLS/`, `02-DOCS/`, el directorio de configuración de tu agente y `.rsc.json` dentro del repo. Si lo quieres probar, en un sandbox y con esos paths en `.gitignore`.
2. **No apuntar `rsc-brain` al NAS de casa.** En ese PC, local o nada. El código de Scalpers no viaja a tu infraestructura.
3. **No usar tu clave personal de OpenCode Go** para código de la empresa. Proveedor aprobado o modelo local.
4. **No copiar las cien skills de Hermes.** Seis aquí, cada una con su examen.
5. **No poner GGA como única puerta.** Es juicio, no mecanismo. Advisory en commit, bloqueante solo en CI y solo para `BLOCKER` y `CRITICAL`.
6. **No auto-mergear a `main`.** Ni con L3.

## Decisiones que necesitan tu OK

1. Qué proveedor de modelo está aprobado en la empresa.
2. Si puedes añadir `.pre-commit-config.yaml` y un job de CI.
3. Si puedes crear una base de datos desechable para los tests.
4. Si el repo admite `.opencode/` y `AGENTS.md` en el árbol, o hay que mantenerlo fuera de git.

## Índice y enlaces

- [[00-Inicio]]
- [[Lauren-Tan-Metodo-Agentes-Plan-2026-11-17]]
- [[Lauren-Tan-2026-11-17/transcripcion-curada-ES|Transcripción curada]]

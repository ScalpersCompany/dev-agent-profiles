---
name: factorlibre-mr-preflight
description: "Preflight de MR en scalpers-v11 (FactorLibre)."
version: 1.1.0
author: Skippy (Nicolás Ramos)
license: MIT
platforms: [linux, windows, macos]
metadata:
  hermes:
    tags: [mr, gitlab, factorlibre, scalpers-v11, odoo-11, preflight, code-review]
    category: software-development
    related_skills: [odoo-11-code-review, gitlab, odoo-11-standards]
---

# Preflight de MR en scalpers-v11

## When to Use

Antes de `git push` y de abrir o actualizar un merge request en
`odoo-11/scalpers-v11` o en los repos hermanos de FactorLibre. También al
responder a una revisión: el mismo patrón sirve para saber qué van a mirar y
cómo contestar.

## Regla de oro

El primer revisor eres tú. El MR se abre cuando el diff ya cumple este
checklist; la revisión de FactorLibre no es la primera pasada. Un MR con
bloqueantes evidentes consume una ronda, retrasa el merge y deja el trabajo
marcado como «no revisado».

## Flujo

1. Rebase sobre `origin/master` y resuelve conflictos **antes** de abrir el MR.
2. Ejecuta el preflight: `python3 scripts/preflight_mr.py --base origin/master`.
3. Corrige todos los `ERROR` y revisa cada `WARN`. Los `INFO` son contexto.
4. Pasa `pre-commit run --files <cambiados>` y los tests en una base con el
   **closure de `depends`** (como el CI), no en la base de desarrollo completa.
5. Abre el MR con `assets/mr-template.md`: descripción, issue enlazada, criterios
   de aceptación, cómo se ha probado y orden de despliegue.
6. Responde a los hallazgos en **commits nuevos**, sin squash hasta el merge y
   sin resolver los hilos (los cierra el revisor).

## Checklist

### 1. Alcance

- [ ] Un MR = una tarea. No mezclar refactor, formateo masivo, traducciones de
      otro módulo ni «de paso».
- [ ] La issue está enlazada y el MR dice qué requisito cumple y cómo se prueba.
- [ ] Si depende de otro MR, se dice y se mergea primero; no se apoya la rama en
      commits de una rama ya mergeada con squash.
- [ ] Si el alcance crece, se divide el MR o se documenta y se valida en la issue.

### 2. Rama y commits

- [ ] `git fetch && git rebase origin/master`; sin conflictos y sin commits por
      detrás.
- [ ] Mensajes de commit en conventional commits (`feat(scope): ...`,
      `fix(scope): ...`), sin `WIP`, `fix`, `cambios` ni `desarrollo`.
- [ ] Commits nuevos para cada corrección de revisión; `squash` solo al final.
- [ ] Sin ficheros ajenos: ni `.bak`, ni scripts sueltos, ni `odd/`, ni capturas
      fuera de `static/`.

### 3. Manifest

- [ ] Versión `11.0.x.y.z`: `x` si cambia el modelo de datos o las vistas y
      puede requerir migración; `y` si hay que actualizar el módulo; `z` si no.
- [ ] Si otra MR del mismo módulo está abierta y también sube la `version`, tu rama
      chocará en el agregado de test y luego en master: la segunda que mergea es la que
      ajusta la versión, y eso no se resuelve reordenando el test.
- [ ] `depends` completo: todo modelo, vista, xmlid o import que se use. Un
      `depends` incompleto no falla con la base completa y revienta en el CI.
- [ ] Sin dependencias redundantes que ya llegan por otro módulo.
- [ ] Datos con `<data noupdate="1">` cuando el cliente los edita.
- [ ] Assets en `views/assets.xml`, no en el manifiesto.
- [ ] `application: True` solo si debe aparecer en Aplicaciones.

### 4. Modelo y datos

- [ ] `_description` en cada modelo; `help` en cada campo nuevo o modificado
      (qué representa, unidad/formato y efecto).
- [ ] `_sql_constraints` si hay unicidad real; `ondelete` explícito.
- [ ] `index=True` en campos que se filtran o buscan mucho (`pos.order`,
      `stock.move`, códigos y referencias).
- [ ] Si se renombra o elimina un campo persistido: migración, no solo cambio de
      código. Si el módulo es nuevo, la carga inicial va en `post_init_hook`
      (`migrations/11.0.1.0.0/` no se ejecuta al instalar).
- [ ] Carpeta de migración nombrada con la versión **nueva** del manifiesto
      (`11.0.1.6.0` para una versión `11.0.1.6.0`), nunca con una intermedia: Odoo 11
      solo ejecuta carpetas con `instalada < carpeta <= nueva`
      (`odoo/modules/migration.py`), así que si otra rama despliega antes esa
      intermedia tu migración no corre y no da ningún error.
- [ ] Migración idempotente, con `limit`, sin `env.ref` que no se usa, sin
      `search` sin `limit=1`, sin booleanos que quedan `NULL` (el cron filtra
      `expired = FALSE` y `NULL` no entra), sin `cr.commit()` innecesario.
- [ ] Nada destructivo sin log, dry-run o respaldo.

### 5. ORM y Odoo 11

- [ ] `@api.multi`/`@api.model` correctos; `ensure_one()` en métodos de un solo
      registro; `for record in self` en constrains.
- [ ] `super()` sin `(Clase, self)` en Python 3; `browse()` en vez de
      `search([('id', '=', x)])`.
- [ ] `float_compare` para importes y cantidades; `fields.Datetime.now()` (UTC),
      no `datetime.now()`.
- [ ] Sin `getattr(obj, 'campo_propio', default)`: enmascara errores de nombre.
- [ ] Sin `search` dentro de bucles; `read_group` para agregados; `limit` cuando
      se espera un registro.
- [ ] No reimplementar `compute_all`, `_amount_all` ni cálculos del core: usa la
      opción nativa o reutiliza el método.
- [ ] Sin `@api.one`, `f-strings`, `type="json"` ni sintaxis posterior a v11.

### 6. Seguridad

- [ ] `ir.model.access.csv` para cada modelo nuevo, incluidos `TransientModel`;
      `ir.rule` para lo que el dominio de la vista no protege.
- [ ] `sudo()` justificado; nunca en controllers por defecto.
- [ ] Sin tokens de administrador, secretos, credenciales ni datos personales en
      código, logs o tests.
- [ ] SQL parametrizado; sin `eval`/`exec`; sin `search([])` sin dominio.
- [ ] Si es «solo lectura», el cursor `READ ONLY` no se puede cerrar con un
      `commit()` de una acción publicada.

### 6.1 Credenciales y superficie de lectura

El conector no es la única puerta: la interfaz y XML-RPC usan la misma ACL.
Un campo con la contraseña de un carrier sin `groups` la deja legible para
cualquier comercial, aunque el módulo del conector la filtre por nombre.

- [ ] Todo campo que guarde, derive o cachee una credencial (password, token,
      refresh token, secreto de webhook, clave privada, passphrase en base64,
      hash de contraseña) lleva `groups` restrictivo y su modelo no concede
      lectura a grupos operativos.
- [ ] Los modelos de configuración de integraciones (`*.config`, `*.backend`,
      `*.webhook`) se tratan como sensibles enteros: bloqueados en el conector
      y con ACL de lectura de administrador.
- [ ] Un campo derivado cuenta igual que el original:
      `bpost_passphrase_encoded` es `base64("cuenta:contraseña")` y no tenía
      `groups`, mientras que `bpost_password` sí.
- [ ] Un hash no es la contraseña, pero permite ataque offline: `password_crypt`
      y los `*_hash` tampoco se exponen a grupos operativos.
- [ ] `groups=` oculta al leer, pero el dominio, el `order` y el `groupby` no lo
      respetan (ver `odoo-11-standards`): la ACL es la frontera real.

Checklist completa, patrones que fallan y las cuatro puertas: skill
`odoo-11-credential-security`.

Comando (sale con 1 si hay credenciales legibles por no administradores):

```bash
python3 scripts/scan_secret_fields.py --root odoo/custom/src
```

Salida: `modelo | campo | fichero:línea | grupos con lectura`. Revisa cada
`claro`; los `hash` se valoran aparte. No lee `ir.rule` ni grupos heredados:
es un filtro para revisar a mano, no un veredicto.

### 7. JS / POS

- [ ] `this` correcto: arrow functions o `self` guardado; no usar `self` en una
      función suelta.
- [ ] `const` no se reasigna; `if (x)` en vez de `!= null`; `?.` no es seguro en
      v11.
- [ ] `on`/`off` con la **misma** función; el socket guarda un solo handler por
      evento: un `off` sin handler borra el de otro widget.
- [ ] `close_popup()`/`_super()` en las salidas del popup; no `trigger('click')`
      para abrir diálogos que el usuario no ha pedido.
- [ ] Campos nuevos del POS en `export_as_JSON` **y** `init_from_JSON`; si no, se
      pierden al refrescar.
- [ ] `_t()` con `_.str.sprintf` para cadenas con parámetros; cadenas en inglés.

### 8. Vistas, XML y traducciones

- [ ] `attrs`/`invisible` de v11; todo campo citado existe en la vista.
- [ ] Herencia por xmlid, `position` justificado, sin tocar el core.
- [ ] Filtros: `separator` entre grupos; los filtros de un mismo grupo se unen
      con OR y pueden no filtrar nada.
- [ ] IDs únicos en XML; sin `edit="false"`; `merge_range` coherente con las
      columnas.
- [ ] `.po` solo con las cadenas de la tarea; no perder traducciones ni meter
      cambios de otro entorno; `es.po`/`es_ES.po` y portugués si aplica.

### 9. Tests

- [ ] Un test que falla sin el cambio y pasa con él; casos límite que la regla
      nombra (sin registro, duplicado, vacío, multi-compañía, concurrencia).
- [ ] `--test-enable` ejecutado de verdad, en base limpia con el closure de
      `depends`; no en la base de desarrollo con todo instalado.
- [ ] Sin tests desactivados, comentados, no importados ni `skipTest` para poner
      el CI en verde.
- [ ] Sin dependencia de módulos que el CI no instala; si el test necesita un
      glue, se declara o se salta con motivo.
- [ ] `TransactionCase`/`SavepointCase`; `@at_install(False)`/`@post_install(True)`
      en v11; sin `cr.commit()` en tests; mock de `urlopen`, no saltar la función.
- [ ] Datos de prueba válidos (código de barras, `default_code`, impuestos) que
      cumplan las constraints que el CI carga de verdad.

### 10. Documentación y despliegue

- [ ] `README.rst` del módulo y `readme/HISTORY.rst` o `CHANGELOG.md` si cambia
      el comportamiento.
- [ ] Docstring en métodos públicos y comentario donde la lógica no se deduce.
- [ ] Descripción del MR con contexto, caso real, issue y pasos de prueba.
- [ ] Orden de despliegue: módulos a actualizar, migración, configuración, cron,
      colas, dependencias externas y rollback.

## Lo que bloquean siempre

1. Tests desactivados o no importados para que el CI pase.
2. Código comentado o muerto que llega a master.
3. Migración ausente al renombrar o borrar algo persistido; migración que no
   corre en una instalación nueva.
4. `depends` incompleto o xmlid de otro módulo sin declarar.
5. Reimplementar a mano un cálculo del core (`compute_all`, `_amount_all`,
   redondeos) en vez de usar la opción nativa.
6. `sudo()` en controllers, tokens de administrador o permisos de más.
7. Rama apoyada en otra rama ya mergeada: el diff enseña trabajo ajeno y da
   conflicto.
8. Diff gigante por formatear todo el fichero o por mezclar traducciones de otro
   entorno.
9. Lógica fiscal, de stock o de devoluciones sin ningún test.
10. `search` en bucle, `ensure_one` ausente, `float` sin `float_compare`,
    `search` sin `limit` en migraciones, cron sin `ir.cron`, `retry_pattern` con
    `FailedJobError`.
11. Credenciales en un campo sin `groups` y ACL de lectura para comerciales,
    stock o empleado; también el campo derivado que las copia (base64, hash,
    refresh token). El escáner del checklist las lista.

## Cómo escriben el veredicto

- **Tier 1 (Quick)**: pocos ficheros y líneas. Revisión corta, sugerencias.
- **Tier 2 (Standard)**: módulo o flujo con tests. Tabla de hallazgos.
- **Tier 3 (Deep)**: core, migraciones, seguridad, fiscalidad, multi-compañía.
  Informe largo con bloqueantes, importantes, sugerencias y validación contra la
  issue.

Cabecera típica: MR, issue, rama, `HEAD` revisado, tier, ficheros, líneas,
resultado del pipeline, bots externos. Severidades 🔴 bloqueante / 🟡 importante /
🔵 sugerencia / ℹ️ info. Cada hallazgo con `fichero:línea`, cita del core y
reproducción con números. En la segunda ronda, tabla de estado por hallazgo con
el SHA de cada corrección y veredicto nuevo.

## Cómo responder

1. **Contesta contra HEAD, no contra la posición del hilo.** La posición de un
   hilo apunta a una versión antigua del diff; tras varias rondas de `fix(...)`
   el hallazgo puede estar ya cerrado. Antes de escribir, busca el mecanismo en
   el árbol actual (la guardia, el parámetro, el método) y localiza el commit
   que lo introdujo:

   ```bash
   git log -S"<simbolo>" --format="%h %s" -- addons/<modulo>
   ```

   La respuesta lleva `fichero:línea` y el SHA, nunca una promesa de que se va a
   arreglar.
2. **Un hilo abierto no es trabajo pendiente.** Los hilos se quedan abiertos
   porque nadie contestó, no porque el código siga mal: el recuento de
   `blocking_discussions_resolved: false` no es la cola de trabajo, el árbol es.
   Revisa los hallazgos uno a uno antes de abrir un solo fichero.
3. Un commit por bloque de hallazgos, con mensaje `fix(scope): ...`; di qué
   commit cierra cada punto. Tabla `punto | estado | commit`; sé explícito con
   lo que no se ha tocado y por qué.
4. No resuelvas los hilos: el revisor los cierra. Solo si está cerrado del todo
   y es evidente, ciérralo, y dilo en la respuesta. Si una sugerencia de estilo
   no se aplica, dilo y ofrece el commit aparte; no lo resuelvas en silencio.
5. Si no estás de acuerdo, argumenta con `fichero:línea`, una prueba o una cita
   del core; no con una opinión.
6. Pide re-review solo cuando el pipeline esté verde y los puntos estén cerrados.
7. **Escribir en GitLab exige un token con scope `api`.** Compruébalo antes de
   prometer que vas a contestar o resolver:

   ```bash
   curl -s --header "PRIVATE-TOKEN: $TOKEN" \
     https://<host>/api/v4/personal_access_tokens/self   # mira "scopes"
   ```

   Con solo `read_api` (el caso del token de `~/.git-credentials`) la API
   devuelve `403 insufficient_scope` tanto en `POST .../discussions/<id>/notes`
   como en `PUT .../discussions/<id>?resolved=true`, y el intento no publica
   nada. En ese caso deja los textos listos para pegar (uno por hilo, con
   `fichero:línea` y SHA) y pide un token con `api`. Receta de endpoints en
   `references/api-hilos-mr.md`.

## Comandos

```bash
# Preflight del diff completo
python3 scripts/preflight_mr.py --base origin/master --head HEAD

# Pre-commit sobre los ficheros del MR
pre-commit run --files $(git diff --name-only origin/master...HEAD)

# Tests en una base limpia, con el closure de depends
odoo -d <base_temporal> -i <modulos> --test-enable --stop-after-init

# Credenciales legibles por no administradores (interfaz y RPC)
python3 scripts/scan_secret_fields.py --root odoo/custom/src
```

## Instalación en otros agentes

La fuente es esta skill en `~/.hermes/skills/software-development/`. Para copiarla
a Claude Code, OpenCode, Codex, pi/gentle-shell y la base compartida `~/.agents`:

```bash
bash scripts/install-to-editors.sh
```

El script es idempotente y solo toca el directorio de esta skill en cada destino.
Comprueba el resultado con el `sha256` que imprime al final.

## Referencias

- `references/estudio-mrs-2024-2026.md` — estudio completo de 607 MRs y 1.209
  notas: quién revisa, cómo, qué bloquea y métricas.
- `references/metrics-mrs-2024-2026.json` — métricas crudas para recalcular las
  cifras del estudio.
- `references/patrones-y-ejemplos.md` — catálogo de patrones con ejemplos reales
  y la corrección esperada.
- `references/api-hilos-mr.md` — endpoints para leer MRs y hilos, contestar,
  resolver y comprobar los scopes del token.
- `assets/mr-template.md` — plantilla de descripción de MR.
- `scripts/preflight_mr.py` — comprobaciones automáticas sobre el diff.
- `scripts/scan_secret_fields.py` — campos con credenciales legibles por
  grupos no administradores (interfaz y XML-RPC, no solo el conector).
- `scripts/install-to-editors.sh` — copia la skill a los otros agentes.

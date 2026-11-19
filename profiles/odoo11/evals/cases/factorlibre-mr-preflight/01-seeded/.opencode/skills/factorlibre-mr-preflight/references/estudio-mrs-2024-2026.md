# Estudio de los MRs de `odoo-11/scalpers-v11` (nov 2024 – nov 2026)

> Estudio interno. No se publica ni se cita fuera del equipo. Las conclusiones
> se basan en 607 MRs y 1.209 notas humanas descargadas por API el 2026-11-14.
> Cada cifra se puede recalcular desde los JSON guardados en el workspace del
> estudio; no se ha estimado ninguna a ojo.

## 1. Resumen ejecutivo

- **607 MRs** creados entre el 2024-11-14 y el 2026-11-13: 549 mergeados, 32
  cerrados y 26 abiertos.
- **221 MRs (36 %)** tienen al menos una nota humana; **386 (64 %)** no tienen
  ninguna. Ese 64 % no significa que no se revisen: incluye merges de
  dependencias, cambios de una línea, actualizaciones de versión y MRs de
  `gitlab_odoo` que se mergean con `/flbot`. La revisión real se concentra en los
  MRs con lógica.
- **1.209 notas humanas**: 934 inline (77 %) y 275 generales (23 %). Las inline
  son el 77 % del volumen: el revisor trabaja sobre la línea, no solo en la nota
  general.
- **16 cuentas de FactorLibre confirmadas por el email de sus commits y con
  actividad de revisión** concentran **545 notas en 126 MRs**. Los dos primeros
  (sushan.voong y daniel.duque) firman el **53 %** de esas notas.
- **9 revisores de Scalpers** añaden 354 notas en 127 MRs; **19 cuentas sin
  dominio confirmado** añaden 286 notas en 84 MRs. Varias de estas últimas
  (jesus.lorenzo, nathalia.muro, almudena.delapuente) producen los informes más
  largos y parecen del equipo de FactorLibre, pero no se ha podido confirmar el
  dominio; se citan aparte.
- El patrón es estable en los dos años: **hilo inline en la línea exacta + nota
  general con veredicto**, severidades y, desde 2026, informes estructurados por
  tiers en los MRs grandes.
- Lo que más bloquea, por orden de impacto: tests desactivados o ausentes en
  lógica crítica, migraciones que no se ejecutan o no son idempotentes,
  `depends` incompletos, reimplementar cálculos del core, `sudo()`/tokens de más,
  ramas apoyadas en otra rama ya mergeada y diffs gigantes por formateo.

## 2. Metodología y límites

1. Listado por API (`GET /projects/321/merge_requests`) con `state=all`,
   `created_after=2024-11-14T00:00:00Z`, `per_page=100`, 7 páginas: 607 MRs.
2. Para los 221 con `user_notes_count > 0`, descarga de
   `GET /merge_requests/:iid/discussions?per_page=100`; se descartan las notas
   `system` (aprobaciones, cambios de estado, merges) y se quedan 1.209 notas
   humanas.
3. Clasificación por autor, inline (`position`) o general, MR, módulo del
   `new_path`, fecha y longitud. La matriz revisor → autor se calcula con el
   autor del MR, no con el autor de la nota.
4. Confirmación del dominio: se lee `author_email` del commit del MR para las
   cuentas que **autoran** MRs; para las que solo revisan no hay email público y
   se marcan como «sin dominio confirmado». No se ha supuesto que una cuenta sea
   de FactorLibre por su nombre.
5. Lectura manual de las 35 notas más largas, de las 168 notas generales y de
   las 623 notas inline de los revisores de FactorLibre; en particular, de las
   395 notas inline de los 14 módulos con más revisión. El resto se ha
   clasificado por palabras clave; por eso las frecuencias temáticas se citan
   como «notas que mencionan», no como una codificación estadística cerrada.
6. **Límite**: los 386 MRs sin notas no tienen contenido de revisión que
   analizar. Se cuentan para las métricas de cobertura, no para el patrón.

## 3. Quién revisa

### 3.1. FactorLibre confirmado por email de commit

| Cuenta | Notas | MRs | Inline | Generales | Media de caracteres |
|---|---:|---:|---:|---:|---:|
| sushan.voong | 154 | 23 | 140 | 14 | 246 |
| daniel.duque | 136 | 38 | 115 | 21 | 294 |
| luisalejandro.sandes | 84 | 18 | 71 | 13 | 134 |
| ivan.bosquez | 29 | 10 | 21 | 8 | 768 |
| aritz.olea | 28 | 14 | 12 | 16 | 272 |
| sergio.bustamante | 28 | 10 | 19 | 9 | 153 |
| pablo.calvo | 22 | 14 | 20 | 2 | 286 |
| juancarlos.jaen | 19 | 11 | 9 | 10 | 105 |
| joan.aldabo | 14 | 5 | 8 | 6 | 161 |
| abril.cantarero | 10 | 6 | 8 | 2 | 112 |
| mariano.martinez | 6 | 4 | 4 | 2 | 687 |
| daniel.amores | 6 | 2 | 4 | 2 | 706 |
| oscar.indias | 4 | 4 | 2 | 2 | 1.527 |
| alvaro.rollan | 3 | 3 | 0 | 3 | 124 |
| alejandro.vallejo | 1 | 1 | 1 | 0 | 9 |
| zahra | 1 | 1 | 0 | 1 | 285 |

**Lectura**: sushan y daniel.duque son el núcleo. Luis Alejandro Sandes es el
tercer revisor por volumen y el que más insiste en el proceso (commits, ramas,
histórico). Aritz Olea y Juan Carlos Jaén hacen más notas generales que inline:
son revisores de arquitectura y de validación contra la issue. Iván Bósquez,
Mariano Martínez, Daniel Amores y Óscar Indias escriben menos notas pero muy
largas: sus MRs suelen llevar informe estructurado.

### 3.2. Scalpers (también revisan, pero no es el foco del estudio)

| Cuenta | Notas | MRs |
|---|---:|---:|
| farcos.scalperscompany | 87 | 26 |
| rbajona.scalperscompany | 60 | 20 |
| parchanco.scalperscompany | 45 | 18 |
| jregalado | 39 | 12 |
| irestoy.scalperscompany | 39 | 17 |
| gcaminero.scalperscompany | 35 | 19 |
| elopez.scalperscompany | 26 | 10 |
| amunoz.scalpers-v11 | 19 | 3 |
| iales.scalperscompany | 4 | 2 |

### 3.3. Cuentas sin dominio confirmado (revisores activos)

| Cuenta | Notas | MRs | Inline | Generales | Media |
|---|---:|---:|---:|---:|---:|
| jesus.lorenzo | 69 | 12 | 64 | 5 | 447 |
| adriana.saiz | 50 | 8 | 40 | 10 | 478 |
| david.alonso | 25 | 7 | 16 | 9 | 721 |
| asier.neira | 24 | 10 | 22 | 2 | 318 |
| alejandro.jicheung | 18 | 4 | 16 | 2 | 196 |
| alex.caro | 18 | 7 | 13 | 5 | 205 |
| rodrigo.bonilla | 13 | 4 | 9 | 4 | 339 |
| maria.lopez | 12 | 2 | 12 | 0 | 203 |
| alvaro.gomez | 11 | 5 | 6 | 5 | 417 |
| nathalia.muro | 9 | 6 | 0 | 9 | 2.779 |
| almudena.delapuente | 8 | 2 | 5 | 3 | 1.442 |
| julio.cabrerizo | 7 | 5 | 4 | 3 | 96 |
| alejandro.roa | 6 | 2 | 5 | 1 | 141 |
| alvaro.marcos | 5 | 3 | 1 | 4 | 214 |
| bencoronel | 4 | 3 | 3 | 1 | 276 |
| luis.salvatierra | 2 | 1 | 0 | 2 | 78 |
| daniel.alvaro | 2 | 1 | 2 | 0 | 409 |
| lucia.marchal | 2 | 2 | 0 | 2 | 5 |
| ismael.jara | 1 | 1 | 1 | 0 | 17 |

No se afirma que todas sean de FactorLibre. Lo que sí se puede afirmar es que
revisan MRs de otros y que sus notas siguen el mismo patrón formal. Los informes
de 2.779 y 1.442 caracteres de media son el formato estructurado descrito abajo.

## 4. Cómo revisan

### 4.1. Dos capas

1. **Hilos inline** en la línea exacta del diff. Es el 77 % de las notas. Ahí van
   el fallo concreto, la pregunta, el snippet corregido o el enlace al core.
2. **Nota general** al final del MR con el veredicto, los bloqueantes que no
   caben en una línea y las instrucciones de proceso (rebase, commits, hilos,
   despliegue).

### 4.2. Formato clásico (2024–2025)

- Saludo con mención (`Buenas @autor`).
- Bloques `## Bloqueante`, `## Importante`, `## Sugerencia`, `## Despliegue`,
  `## Pendiente de confirmar`.
- A veces sin tabla; los puntos van numerados y con `fichero:línea`.
- Cierre: «te lo dejo aprobado», «LGTM», «lo veo correcto», «puedes
  desplegarlo en test».

### 4.3. Formato estructurado (2026)

Aparece en 9 MRs, los grandes. Cabecera:

```text
MR, issue, rama → master, HEAD revisado (SHA), Tier 1/2/3
Ficheros, líneas añadidas, módulos, pipeline, bots externos
Tabla de resumen: tier, ficheros, pipeline, tests, % de cumplimiento de la issue
```

Cuerpo:

- `## 🔴 Bloqueantes` numerados `B1..Bn`, con `fichero:línea`, cita del core y
  reproducción con números.
- `## 🟡 Importantes` `I1..In`, normalmente en tabla.
- `## 🔵 Sugerencias` `S1..Sn`.
- `## Comprobado sin problemas`: lo que se ha verificado y no es un fallo, para
  que el autor no lo discuta.
- `## Validación contra el plan / la issue`: tabla requisito → estado → test.
- `## Cobertura de tests`: qué se prueba y qué no.
- `## Veredicto`: 🔴 requiere cambios / 🟡 aprobar con cambios / 🟢 aprobar.
- Bloque HTML oculto `gextia-review-findings` con JSON de hallazgos (severidad,
  fichero, línea, regla, resumen). No es un formato de Odoo: es la herramienta
  de revisión del equipo.

### 4.4. Rondas

- La segunda revisión **no reestrena** el MR: tabla de estado por hallazgo con
  `✅ Resuelto` / `⚠️ Retirado` / `❌ Pendiente` y el SHA de cada corrección.
- Si el autor cambia lógica que ya estaba aprobada, el revisor **retira la
  aprobación** y vuelve a revisar (MR !2223).
- El autor responde en el hilo con el commit; no resuelve el hilo. Los hilos los
  cierra el revisor.
- La aprobación formal la da el revisor humano, no un bot ni la API.

### 4.5. Qué exigen de fondo

- Cita `fichero:línea` del código revisado y, cuando aplica, del core de Odoo
  (`addons/...:línea`) para demostrar que la API existe en v11.
- Reproducción con números concretos: «10 líneas de 0,30 € con IVA 21 % dan
  0,60 en vez de 0,63».
- Alternativa nativa antes que override: `round_globally`, `compute_all`,
  `float_compare`, `close_popup`, `_super`, `browse`.
- Tests con nombre y casos; no vale «probado en local».
- Migración cuando se renombra o borra algo persistido.
- Plan de despliegue: módulos a actualizar, orden, configuración, cron, colas,
  rollback.

## 5. Qué miran y qué bloquean

### 5.1. Tests

- **Desactivados para poner el CI en verde** es el bloqueante más grave. En el
  MR !2446 se dejan de importar dos ficheros de test (`test_fix_quant_stock` y
  `test_hai_outbound_bypass_reservation`): 16 tests fuera de la ejecución, de
  los que solo 5 fallaban. El revisor lo detecta leyendo `tests/__init__.py` en
  el diff y comparando el número de tests de la pipeline.
- **Sin tests en lógica crítica**: fiscalidad (MR !2430), importación EDI
  (!2376), devoluciones y defectos (!2452), migración de loyalty (!2355). No es
  «falta un test»: es «esta lógica falla en silencio y no hay nada que lo
  detecte».
- **Tests que dependen de un módulo que el CI no instala**: en !2435 el test de
  la factura agrupada usaba `pos_session_grouped_invoice_coupon_tracking`, que
  no está en el closure de `depends`; en local pasaba y en CI fallaba. La
  revisión pide ejecutar en una base con **solo el closure del manifest**.
- **Test que salta la función en vez de hacer mock**: en !2382 el test salta
  toda la función; el revisor pide mockear `urlopen` y probar el camino real.

### 5.2. Migraciones y datos

- **Migración ausente** al renombrar o borrar un campo persistido (MR !2430,
  !2419).
- **Migración que no se ejecuta**: en !2355 el backfill está en
  `migrations/11.0.1.0.0/post-migration.py` de un módulo nuevo. En una
  instalación nueva el script no corre (`migration.py:108`), así que el backfill
  es código muerto. La corrección es `post_init_hook`.
- **Migración que rompe**: `env.ref("pos_coupons.basic")` declarado y no usado
  aborta si el xmlid no existe; `search()` sin `limit=1` deja `site_id = False`
  y el SQL peta con `invalid input syntax for type integer: "False"`; el SQL no
  es idempotente (MR !2272).
- **Booleanos que quedan `NULL`**: en !2392 el `INSERT` crudo no pone `expired` y
  el cron filtra `expired = FALSE`; esas filas no caducan nunca.
- **CTE mal agrupadas**: el saldo se lee por país, pero la migración agrupa solo
  por cliente y resta el saldo de ES contra el de PT (!2392).
- **Commit dentro de un job o migración**: rompe la transacción y deja estados a
  medias; el revisor pide savepoint o justificación (!2355).
- **Nada destructivo sin log ni dry-run**: borrar historial o reconstruir saldos
  exige enumerar, contar, respaldar y poder revertir.

### 5.3. Manifest y dependencias

- **`depends` incompleto**: el código usa `sale`, un campo de `scalpers_partner`
  o un xmlid de otro módulo y no está declarado (MR !2452, !2250, !2074). No
  falla con la base completa; revienta en el CI o al instalar el módulo solo.
- **`depends` redundante**: `base_vat` ya llega por `base_vat_sanitized`
  (!2106); `point_of_sale` ya depende de `base` (!2113).
- **Versión**: `11.0.x.y.z`, primera versión de un módulo nuevo `11.0.1.0.0`
  (!2090); se sube `x` si hay cambio de modelo/vistas con posible migración, `y`
  si hay que actualizar el módulo, `z` si no.
- **README**: módulo nuevo o cambio funcional sin README/HISTORY. El revisor lo
  pide como parte del MR, no como tarea aparte.

### 5.4. ORM y Odoo 11

- `search` en bucle o por cada línea: se sustituye por `browse` o por un
  `search` único (!2430, !2376).
- `search` sin `limit=1` cuando se espera un registro; `_gather(strict=True)`
  puede devolver varios quants y `quant.quantity` peta con `Expected singleton`
  (!2415).
- `ensure_one()` ausente en métodos de un registro; `for record in self` en
  constrains (!2305).
- `float_compare` para importes y cantidades; comparar floats con `>` o `!=`
  marca quants sanos como corruptos (!2415).
- `getattr(obj, "campo_propio", default)` enmascara un nombre mal escrito: en
  !2272 el POS recibe siempre `False` porque el campo es `site_fidelized_tpv` y
  se lee `fidelized_tpv`.
- `super()` sin `(Clase, self)` en Python 3; `browse()` en vez de
  `search([("id", "=", x)])`.
- `datetime.now()` es hora del servidor; `fields.Datetime.now()` es UTC. Y
  `pytz.timezone(pytz.utc)` peta si el usuario no tiene `tz` (!2343).
- No reimplementar `compute_all`/`_amount_all`: se pierde el tratamiento de
  impuestos `fixed`, `division`, `group`, `price_include`, multi-compañía y
  redondeo global (!2430).

### 5.5. Seguridad

- `sudo()` en controllers: en !2250 se repite en cada endpoint; el revisor pide
  quitarlo o justificarlo.
- Tokens de administrador en el MCP: un token de `base.group_system` puede leer
  `ir.config_parameter`, credenciales y datos personales. La revisión de !2462
  pide rechazar administradores, bloquear modelos sensibles y acotar por token.
- `READ ONLY` no es suficiente si una acción publicada puede hacer `commit()`:
  el `SET TRANSACTION READ ONLY` vale para la transacción en curso; tras un
  `commit()` la siguiente admite escritura (!2462).
- ACL para modelos nuevos, incluidos `TransientModel`; reglas `ir.rule` para lo
  que el dominio de la vista no protege (!2300).
- Sin secretos, tokens ni datos de cliente en código, logs o tests.

### 5.6. JS / POS

- `self` en una función suelta: `ReferenceError` que se traga el `try` y deja el
  patrón en `null` (!2074).
- `const` reasignado: `TypeError: Assignment to constant variable` con
  `"use strict"` (!2074).
- `if (x != null)` acepta `false`, `0` y `''`; en el POS hay que usar `if (x)`
  (!2074).
- `on`/`off` sin la misma función: el socket guarda un solo handler por evento,
  así que `off("scanned_tag")` borra el de la pantalla de venta (!2074, !2391).
- `trigger('click')` sobre `.deleteorder-button` abre el diálogo de borrar
  pedido, no borra: el `_super()` lo cierra y el `confirm` no se ejecuta
  (!2074).
- `close_popup()` en todas las salidas del popup; no dejar estado a medias
  (!2113).
- Campos nuevos del POS en `export_as_JSON` **y** `init_from_JSON`; si falta el
  segundo, se pierden al refrescar (!2126).
- `_t()` con parámetros debe ser `_.str.sprintf(_t(cadena), params)`; si no, la
  cadena no se traduce (!2070).
- `?.` no es seguro en v11; usar `&&` (!2070, !2359).

### 5.7. Estados, flujos y multi-compañía

- `draft`/`paid` en el TPV: la issue pedía «solo draft» y el código no filtraba
  por estado (!2367).
- `partially_available` no existe en `stock.picking` de v11: es del move; el OUT
  encadenado está en `waiting` y `action_done` no valida nada (!2439).
- `backorder_id` no es neutro: el cron de HAI filtra `backorder_id = False` y el
  conector padre cancela los pickings con `backorder_id` apuntando al original
  (!2351).
- `env.user.company_id` no es la compañía del documento: usar
  `record.config_id.company_id` o `order.company_id` (!2455).
- Multi-compañía en dominios y agrupaciones: enlazar por nombre en vez de por FK
  puede duplicar filas (!2405).

### 5.8. Vistas, traducciones y documentación

- Filtros nuevos dentro de un grupo sin `separator`: se unen con OR y no
  filtran lo que parece (!2422).
- Campo citado en una vista que no existe en el modelo (!2250).
- IDs duplicados en XML (!2377).
- `.po` con cambios masivos o traducciones perdidas (!2106, !2069); solo las
  cadenas de la tarea, en inglés, con `_()`/`_t()`.
- `help` y `string` de campos nuevos; el revisor lo pide y la norma de la casa lo
  exige.

### 5.9. Proceso

- Rebase antes de mergear; ramas 15, 31 o 50 commits por detrás (!1870, !1882).
- Rama apoyada en otra rama ya mergeada con squash: el diff enseña trabajo ajeno
  y da conflicto (!2435).
- Commits nuevos para cada corrección; no squash hasta el merge (!2113).
- Descripción del MR: contexto, caso real, issue, pasos de prueba (!2430, !1900).
- Etiqueta correcta: `~Conector` en vez de `~Pedidos` cuando el cambio es del
  conector (!2109).
- Hilos sin resolver: los cierra el revisor (!2070, !2227).

## 6. Norma escrita y práctica

La plantilla `.gitlab/merge_request_templates/MR.md` del repo dice:

- El primer revisor eres tú: revisa todo el diff, tests y README.
- Descripción detallada; si es un FIX, qué pasaba y cómo se ha corregido.
- Asocia siempre el MR a una tarea.
- Cambios en commits nuevos, sin squash hasta que esté listo para mergear.
- Los hilos abiertos los cierra el revisor; el autor solo si está claro.
- Cuando haya cambios, vuelve a solicitar la revisión.
- Pre-commit instalado en todos los repos.

Checklist de la plantilla: funcionalidad, nombres de funciones y variables,
diseño, complejidad, tests, `depends`, README, mensajes de commit y descripción,
versión `11.0.x.y.z`.

Lo que la plantilla **no** dice y los revisores sí exigen en la práctica:

- `help` en campos nuevos y `README`/`HISTORY` en cambios funcionales.
- Migración cuando se renombra o borra algo persistido, y `post_init_hook` para
  la carga inicial de un módulo nuevo.
- Tests en una base con el closure de `depends` (como el CI), no en la base de
  desarrollo completa.
- No desactivar tests ni código comentado.
- Plan de despliegue y rollback.
- No reimplementar cálculos del core.
- `sudo()` justificado y sin tokens de administrador.

## 7. Métricas

### 7.1. Cobertura por año

| Año | MRs | Con notas | % |
|---|---:|---:|---:|
| 2024 (desde 14/11) | 64 | 21 | 33 % |
| 2025 | 313 | 100 | 32 % |
| 2026 (hasta 13/11) | 230 | 100 | 43 % |

### 7.2. Distribución de notas por MR

- 386 MRs con 0 notas.
- 221 MRs con al menos una nota. El top: !2074 (40), !2113 (36), !2070 (34),
  !2126 (25), !2452 (25), !2227 (23), !2250 (23), !1990 (21), !2305 (19),
  !2300 (18), !2430 (18), !2174 (17), !2069 (16), !2264 (16), !2390 (16).

### 7.3. Veredictos

No todos los MRs llevan veredicto formal. Entre las notas humanas aparecen 37
con algún marcador de «requiere cambios/rechazar», 53 con «aprobado/LGTM» y 31
con «no bloqueante/cambios menores». Son notas, no MRs únicos: un mismo MR puede
tener varios. La conclusión útil no es el porcentaje exacto, sino que **el
veredicto se escribe en la nota general y los bloqueantes van también en hilos
inline**.

### 7.4. Módulos con más revisión inline

| Módulo | Notas inline |
|---|---:|
| pos_sap_integration | 84 |
| scalpers_pos_idcloud_return | 45 |
| scalpers_connector_idcloud_status | 34 |
| scalpers_pos_unique_sequence | 33 |
| scalpers_pos_mobile | 25 |
| scalpers_connector_sap | 23 |
| scalpers_pos_shop | 22 |
| pos_loyalized | 21 |
| scalpers_edi_desadv | 21 |
| scalpers_connector_hai_robotics | 20 |
| scalpers_cumulative_loyaltylion | 18 |
| scalpers_pos_payment_return_control | 17 |
| scalpers_pos_gift_order | 17 |
| scalpers_return_sale_order_from_pos_shopify | 15 |

El TPV y los conectores concentran la revisión. No es casualidad: es donde
están los estados, los importes, los sockets, las devoluciones y los datos de
cliente.

## 8. Recomendaciones para el que abre el MR

1. **No abras el MR hasta que el diff cumpla el checklist.** El primer revisor
   eres tú; la revisión de FL no es la primera pasada.
2. **Ejecuta el preflight** (`scripts/preflight_mr.py`) y corrige los `ERROR`.
3. **Tests en base limpia con el closure de `depends`**, no en la base de
   desarrollo con todo instalado. Es el fallo de CI más repetido.
4. **Si tocas datos, escribe la migración en el mismo MR** y prueba una
   instalación nueva y una actualización.
5. **Si tocas el core o un cálculo, demuestra que la opción nativa no vale** o
   reutiliza el método. No reimplementes `compute_all`.
6. **Rebase antes de abrir** y otra vez antes de mergear. No apoyes la rama en
   otra rama ya mergeada con squash.
7. **Commits nuevos para las correcciones** y tabla de estado en la respuesta;
   no resuelvas los hilos.
8. **Describe el MR** con el caso real, la issue y cómo se ha probado. Una
   descripción vacía es un hallazgo en sí mismo.

## 9. Anexo: MRs citados

| MR | Tema |
|---|---|
| !1870 | rebase, rama 15 commits por detrás |
| !1882 | rama 31/50 commits por detrás |
| !1900 | MR abierto a la rama equivocada, falta descripción |
| !1921 | refactor de devoluciones, comprobaciones perdidas |
| !1927 | copia del core sin todas las comprobaciones |
| !1956 | variable innecesaria, `default_partner_id` de otro módulo |
| !1990 | `float_compare`, `search` doble, `create_from_ui` |
| !2029 | `self`, `then/fail`, pantalla bloqueada |
| !2069 | traducciones perdidas, formateo masivo |
| !2070 | `_t` con parámetros, `?.`, `console.log`, hilos |
| !2074 | `self` inexistente, `const` reasignado, `off` sin handler, `!= null` |
| !2090 | versión `11.0.1.0.0` |
| !2106 | `depends` redundante, `.po` masivo |
| !2109 | etiqueta `~Conector` |
| !2113 | `close_popup`, `_super`, CSS del core, código muerto |
| !2126 | `init_from_JSON`, excepciones de queue_job |
| !2223 | cambio de lógica tras aprobación, retirada de aprobación |
| !2227 | hilos sin resolver, `search` en bucle |
| !2250 | `sudo` en controllers, campo inexistente, HTML no renderizado |
| !2261 | imports sin usar, `search` sin dominio, `_get_status_msg` |
| !2272 | 14 bloqueantes: `.fortmat`, cursor, `Response`, migración, cron |
| !2300 | ACL de TransientModel, variables no usadas |
| !2310 | import ordering, tests ausentes |
| !2314 | `@api.model` con `order`, sin tests |
| !2319 | idempotencia, `@api.model` con `self.gift_card` |
| !2343 | `datetime.now()` vs UTC, `pytz.timezone(pytz.utc)` |
| !2351 | `return` perdido, `backorder_id` |
| !2355 | `post-migration` que no corre, tests de migración |
| !2367 | `draft` vs `paid`, líneas de pago, `RetryableJobError` |
| !2376 | campo que no está en master, `search` por línea, sin tests |
| !2377 | IDs duplicados, `_` sin usar, `False` en JS |
| !2382 | `commit()` en test, `identity_key`, mock de `urlopen` |
| !2391 | `on/off` de socket, `trigger` de otro botón, colisión por nombre |
| !2392 | migración: país, `expired` NULL, idempotencia |
| !2405 | `backorder_id`/FK, multi-compañía, tests |
| !2415 | `ensure_one`, `float_compare`, reservas de quants |
| !2422 | filtros OR sin `separator` |
| !2430 | `round_globally`, `compute_all`, `fixed`/`division`, tests |
| !2435 | rama sobre rama, `.upper()`, tests que se saltan |
| !2439 | `partially_available`, `waiting`, reconciliación de OUT |
| !2446 | tests desactivados, `max()` no acumula |
| !2452 | `depends`, traslado a defectos, sin tests |
| !2455 | `env.user.company_id` vs compañía del documento |
| !2462 | tokens admin, `READ ONLY` con `commit()`, ACL |

## 10. Cómo mantener este estudio

- Guardar los JSON crudos (`mrs.json`, `discussions/`, `notes.jsonl`) junto al
  informe; sin ellos las cifras no se pueden recalcular.
- Repetir el listado con `created_after` y `state=all`; no usar la UI para
  contar.
- Confirmar el dominio por `author_email` del commit, no por el nombre de la
  cuenta.
- Si cambia la plantilla `MR.md`, actualizar la sección 6 y el checklist de la
  skill.

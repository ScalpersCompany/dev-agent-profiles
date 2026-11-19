# Patrones de revisión de FactorLibre y cómo evitarlos

Catálogo extraído de 1.209 notas humanas en 221 MRs de `scalpers-v11`
(2024-11-14 a 2026-11-13). Cada patrón lleva qué se ve en la revisión, por qué
importa y la corrección esperada. Los números de MR son internos y sirven para
volver al hilo original.

## 1. Tests desactivados para poner el CI en verde

**Qué se ve**: el diff toca `tests/__init__.py` y comenta o elimina un
`from . import test_...`; la pipeline pasa porque hay menos tests, no porque el
código esté bien.

**Por qué importa**: es el bloqueante más grave. En !2446 se dejan fuera 16 tests
de los que solo 5 fallaban; el flujo de HAI con `hai_bypass_reservation_update`
se queda sin cobertura. En !2435 un test se salta porque depende de un módulo que
el CI no instala.

**Corrección**: vuelve a importar los tests y adapta los que fallan al cambio.
Si un test no puede correr en CI, sáltalo con `skipTest` y un motivo, pero no
lo borres ni lo comentes.

## 2. Lógica crítica sin tests

**Qué se ve**: módulo de fiscalidad, stock, devoluciones, migración o conector
sin `tests/`, o con tests que solo cubren el caso feliz.

**Por qué importa**: en !2430 se reescribe el cálculo de impuestos de pedido y
factura sin un solo test; en !2376 son 422 líneas de importación EDI sin
cobertura; en !2452 no hay tests en ningún módulo tocado.

**Corrección**: un test por regla, con los casos que la regla nombra: sin
registro, duplicado, vacío, multi-compañía, concurrencia, idempotencia. En v11
usa `@at_install(False)` / `@post_install(True)`; `@tagged` no existe.

## 3. Tests que pasan en local y fallan en CI

**Qué se ve**: el test usa un modelo o un xmlid de un módulo que no está en el
closure de `depends` del módulo testado. En la base de desarrollo está instalado
a mano; en el CI no.

**Por qué importa**: es un falso verde que solo aparece en la pipeline (!2435:
`pos_session_grouped_invoice_coupon_tracking` no está en `depends`, el test de la
factura agrupada falla en CI).

**Corrección**: ejecuta los tests en una base con **solo** el closure del
manifest (`-i <modulo>`), como el CI. Si el test necesita un glue, decláralo o
sáltalo con motivo.

## 4. Migración en la primera versión del módulo

**Qué se ve**: módulo nuevo, versión `11.0.1.0.0`, y un
`migrations/11.0.1.0.0/post-migration.py` con la carga inicial.

**Por qué importa**: en una instalación nueva el script no corre. En v11,
`migration.py:108` corta si el estado es `to install`; en upgrade la condición
`parsed_installed_version < full_version <= current_version` tampoco se cumple
porque antes de `1.0.0` el módulo no existía. El backfill es código muerto y los
saldos históricos quedan a `NULL` (!2355).

**Corrección**: la carga inicial va en `post_init_hook` del manifest. Deja el
script de migración para versiones futuras.

## 5. Migración que rompe o no es idempotente

**Qué se ve**: `env.ref("modulo.xmlid")` declarado y no usado; `search()` sin
`limit=1`; SQL que inserta `site_id = False`; falta `ON CONFLICT`; `commit()`
intermedio; `INSERT` crudo sin los campos obligatorios.

**Por qué importa**: en !2272 el `env.ref` no usado aborta la migración si el
xmlid no existe y el `search` vacío mete `site_id = False` en el SQL
(`invalid input syntax for type integer: "False"`). En !2392 el `INSERT` no pone
`expired` y el cron filtra `expired = FALSE`: esas filas no caducan nunca; la
CTE agrupa solo por cliente y resta el saldo de ES contra el de PT.

**Corrección**: `limit=1` y comprobación de vacío; `ON CONFLICT DO NOTHING` o
`WHERE` idempotente; booleanos con `FALSE` explícito; agrupa por la misma clave
que lee el código; nada de `commit()` dentro del job; prueba la migración en una
copia y en una instalación nueva.

## 6. `depends` incompleto

**Qué se ve**: el código importa `odoo.addons.x`, usa `env['x.y']`, hereda una
vista de `x` o referencia un xmlid `x.*`, y `x` no está en `depends`.

**Por qué importa**: con la base completa no falla; al instalar el módulo solo
revienta con `External ID not found` o `Invalid field` (!2452: falta `sale`;
!2250: falta `scalpers_partner`; !2074: `scalpers_pos_idcloud_pos2`).

**Corrección**: declara el módulo que define el modelo, la vista o el xmlid. Si
la dependencia es circular, extrae un módulo puente en vez de consolidarla.

## 7. `depends` redundante

**Qué se ve**: se añade `base_vat` cuando ya llega por `base_vat_sanitized`, o
`base` cuando ya llega por `point_of_sale`.

**Por qué importa**: ruido y falsa sensación de control; el revisor lo pregunta
(!2106, !2113).

**Corrección**: declara solo la dependencia directa que usas. Si dudas, mira el
manifest del módulo del que ya dependes.

## 8. Versión del manifest

**Qué se ve**: módulo nuevo con `11.0.0.0.0` o `11.0.1.0.9`; cambio de código sin
subir la versión; manifest tocado sin cambiar la versión.

**Por qué importa**: el despliegue y las migraciones se guían por la versión. En
!2090 el revisor pide `11.0.1.0.0` para la primera versión. En !2435 falta subir
la versión de dos módulos antes del merge.

**Corrección**: `11.0.x.y.z`. Sube `x` si cambia el modelo o las vistas y puede
requerir migración; `y` si hay que actualizar el módulo; `z` si no.

## 9. Rama sin rebase o apoyada en otra rama

**Qué se ve**: la rama está 15, 31 o 50 commits por detrás de master; el diff
enseña ficheros de otra tarea; hay conflicto con master; la rama se creó sobre
la de otra tarea que ya se mergeó con squash.

**Por qué importa**: en !2435 la rama sigue sobre los commits sueltos de
`scalpers_sap_417`, que ya está en master con squash; el MR enseña 19 ficheros
cuando el cambio propio son 10, y al resolver el conflicto a mano se pierde el
arreglo del `GIFT_CARD`.

**Corrección**: `git fetch && git rebase origin/master` antes de abrir y antes de
mergear. Si la rama padre ya está en master, rebasa con
`git rebase --onto origin/master <commit-padre>`.

## 10. Diff gigante por formateo o traducciones

**Qué se ve**: el MR formatea todo el fichero, regenera un `.po` desde otro
entorno o mete traducciones de otro módulo. Cientos de líneas que no son de la
tarea.

**Por qué importa**: en !2069 el revisor pide separar el formateo del cambio
real; en !2106 el `.po` trae cambios de conectores y cadenas que pierden la
traducción; en !2435 el diff mezcla la tarea con la rama padre.

**Corrección**: un commit de formateo aparte (o ninguno), y el `.po` solo con las
cadenas nuevas. Si el fichero se regenera, revisa el diff y revierte lo que no
sea de la tarea.

## 11. Código muerto, comentado o imports sin usar

**Qué se ve**: variables que no se usan, imports de más, métodos que nadie
llama, `# TODO`, código comentado, `self` o `bind` inexistentes.

**Por qué importa**: en !2074 sobra `PaymentScreenWidget`; en !2143 `discounts`
se define dos veces; en !2300 `api`, `fields` y `reference` no se usan; en !2113
hay un método que se guarda «para futuro» y no se ejecuta.

**Corrección**: borra lo que no se usa. Si es para una fase futura, va en la
fase futura, no en este MR. Pasa `flake8`/`pylint` antes de abrir.

## 12. Reimplementar el core o pisar `super()`

**Qué se ve**: se copia una función del core «para cambiar una línea», se
recalcula un total a mano o se llama a `super()` y después se sobrescribe el
resultado.

**Por qué importa**: en !2430 se reimplementa `compute_all` y se pierden los
impuestos `fixed`, `division`, `group` y `price_include`; en !1927 faltan
comprobaciones de `create_from_ui` que el core hace antes de procesar el pedido;
en !1967 se copia entero `click_return` y se pierden los `show_popup` de error.

**Corrección**: usa la opción nativa (`round_globally`, `compute_all`,
`_amount_all`), hereda el método y añade solo lo necesario, o extrae un helper
que llame al core. Si de verdad hay que copiar, demuestra por qué y cubre las
comprobaciones que quitas.

## 13. `search` en bucle o sin `limit`

**Qué se ve**: `search` dentro de un `for` por cada línea, `search` por id para
un registro que ya se tiene, `search([])` sin dominio, `search` sin `limit=1`
cuando se espera uno.

**Por qué importa**: en !2430 se hace un `search` por cada grupo de impuestos;
en !2376 se busca por cada línea EDI sobre `pos.order`; en !2261 un `search` sin
dominio sobre `idcloud.backend` puede coger un registro arbitrario.

**Corrección**: `browse` si tienes el id, un `search` fuera del bucle con todos
los ids, `read_group` para agregados, `limit=1` si esperas uno.

## 14. `ensure_one` y `Expected singleton`

**Qué se ve**: un método lee `self.campo` sobre un recordset que puede tener
varios registros; `@api.constrains` recorre `self` sin `for record in self`;
`_gather(strict=True)` devuelve varios quants.

**Por qué importa**: en !2415 `quant.quantity` peta con `Expected singleton`
cuando HAI crea quants duplicados por contención; en !2305 un `@api.constrains`
sin bucle puede petar.

**Corrección**: `self.ensure_one()` al principio si el método es de un registro;
`for record in self` en constrains; `sum(quant.mapped(...))` o `quant[:1]` con
log si el core puede devolver varios.

## 15. Comparar floats sin `float_compare`

**Qué se ve**: `if amount > other`, `if qty != expected`, `==` sobre importes.

**Por qué importa**: en !2415 un epsilon marca un quant sano como corrupto o se
salta un write real; en !1990 el revisor pide `float_compare(order.amount_total,
importe, 2)`.

**Corrección**: `float_compare(a, b, precision_rounding=...)` o
`float_is_zero`. Para moneda usa la precisión de la moneda; para UoM, la del
producto.

## 16. Fechas y zonas horarias

**Qué se ve**: `datetime.now()` en un modelo, `pytz.timezone(self.env.user.tz)`
sin fallback, comparar fechas con la hora del servidor.

**Por qué importa**: en !2343 `datetime.now()` es hora local del servidor y
`pytz.timezone(pytz.utc)` peta con `AttributeError` si el usuario no tiene `tz`.

**Corrección**: `fields.Datetime.now()` (UTC); `tz = self.env.user.tz or "UTC"`
y luego `pytz.timezone(tz)`.

## 17. `sudo()` en controllers y tokens de administrador

**Qué se ve**: todos los endpoints nuevos usan `.sudo()`; el token se acepta
para cualquier usuario, incluido `base.group_system`; no hay lista de modelos
permitidos.

**Por qué importa**: en !2250 el revisor pide justificar cada `sudo`; en !2462
un token de administrador puede leer `ir.config_parameter`, credenciales y datos
personales, y el `READ ONLY` se puede cerrar con un `commit()` de una acción
publicada.

**Corrección**: usa el usuario de la petición; si necesitas `sudo`, justifícalo
y acótalo. Rechaza administradores, bloquea modelos sensibles y permite acotar
por token. Para solo lectura de verdad, usa un cursor propio `READ ONLY` y no
ejecutes acciones que puedan hacer `commit()`.

## 18. ACL de modelos nuevos, incluidos `TransientModel`

**Qué se ve**: modelo nuevo sin `ir.model.access.csv`; `TransientModel` sin
reglas porque «es temporal».

**Por qué importa**: en !2300 se crean dos `TransientModel` sin ACL.

**Corrección**: una línea por modelo y grupo en `security/ir.model.access.csv`,
también para los transient. Si hay multi-compañía, añade `ir.rule`.

## 19. JS del POS: `this`, `self`, `const`, `!= null`

**Qué se ve**: `self` en una función suelta; `const` reasignado; `if (x != null)`
para comprobar si hay valor; `?.` en v11.

**Por qué importa**: en !2074 `parseEpcData` usa `self` y lanza `ReferenceError`
que el `try` se traga; `gs1Formatted` es `const` y se reasigna con `"use
strict"`; `if (sgtin != null)` acepta `false` y crea un binding basura.

**Corrección**: arrow functions o `const self = this`; `let` si se reasigna;
`if (x)` si buscas valor; `&&` en vez de `?.`.

## 20. JS del POS: listeners `on`/`off` y popups

**Qué se ve**: `off("scanned_tag")` sin handler; `trigger('click')` sobre un
botón de otro widget; popup que no llama a `close_popup()`.

**Por qué importa**: el socket del POS guarda **un solo** handler por evento, así
que `off` sin handler borra el de la pantalla de venta (!2074, !2391); en !2074
`trigger('click')` sobre `.deleteorder-button` abre el diálogo de borrar pedido y
el `_super()` lo cierra, con lo que el pedido no se borra; en !2113 el popup no
se cierra y se guarda lo que estaba.

**Corrección**: guarda el handler, registra en `show()` y desregistra en
`close()` con la misma función; usa `close_popup()` y los `click_confirm`/
`click_cancel` del `PopupWidget`; no dispares botones de otro widget.

## 21. JS del POS: `init_from_JSON` y `_t`

**Qué se ve**: campo nuevo en `export_as_JSON` pero no en `init_from_JSON`;
`_t("cadena " + variable)` o `_t` con `%s`.

**Por qué importa**: en !2126 el campo se pierde al refrescar el TPV; en !2070
las cadenas con parámetros no se traducen nunca.

**Corrección**: añade el campo a `init_from_JSON`; para cadenas con parámetros
usa `_.str.sprintf(_t(cadena), params)`.

## 22. Estados y flujos

**Qué se ve**: el código no filtra por el estado que pide la issue; se usa
`partially_available` en `stock.picking`; se valida un OUT en `waiting` con
`action_done`; se enlaza con `backorder_id` sin conocer sus efectos.

**Por qué importa**: en !2367 la issue pedía «solo draft» y el código no filtraba;
en !2439 `partially_available` no existe en el picking de v11 (es del move) y el
OUT encadenado está en `waiting`; en !2351 el cron de HAI filtra
`backorder_id = False` y el conector padre cancela los pickings con
`backorder_id` apuntando al original.

**Corrección**: valida el estado antes de actuar; usa los estados reales de v11
(`draft`, `confirmed`, `waiting`, `assigned`, `done`, `cancel`); si usas
`backorder_id`, revisa quién lo consume y si hay un flag específico
(`no_export_hai`).

## 23. Multi-compañía

**Qué se ve**: `env.user.company_id` para decidir la compañía del documento;
dominios sin `company_id`; enlazar por nombre en vez de por FK.

**Por qué importa**: en !2455 la empresa se toma de `record.config_id.company_id`
y el respaldo es `pos_order_id.company_id`; en !2405 enlazar el pedido por
`pg.name = so.name` puede duplicar filas con tres sociedades.

**Corrección**: la compañía sale del documento (`record.company_id`,
`order.company_id`, `config_id.company_id`); añade `company_id` al dominio cuando
aplique; enlaza por FK.

## 24. Impuestos y redondeo

**Qué se ve**: se recalcula el impuesto a mano; se asume que todos los impuestos
son porcentajes; se ignora `price_include`; se compara el total del pedido con el
de la factura sin probarlo.

**Por qué importa**: en !2430 el override recalcula todos los impuestos si
cualquier línea tiene uno no incluido, y la fórmula `base * amount / 100` falla
con `fixed`, `division` y `group`; el pedido y la factura acaban con totales
distintos. En !2456 se discute el redondeo a un céntimo fijo.

**Corrección**: usa `compute_all`/`round_globally` o limita el override a
`amount_type == 'percent'` y `price_include == False`; redondea con la precisión
de la moneda; prueba pedido y factura juntos, con impuestos incluidos, fijos,
de grupo y negativos.

## 25. Vistas, filtros y traducciones

**Qué se ve**: filtros nuevos dentro de un grupo sin `separator`; campo citado
que no existe; IDs duplicados; `invisible` con expresión; `.po` con cambios
masivos; cadenas en español sin `_()`/`_t()`.

**Por qué importa**: en !2422 los filtros nuevos se unen con OR y no filtran lo
que parece; en !2250 se filtra por `reception_place`, que no existe; en !2377 el
id `retrieve_product_season` se repite; en !2106 el `.po` pierde traducciones; en
!2192 las cadenas están en español.

**Corrección**: `separator` entre grupos; verifica el campo contra el modelo;
IDs únicos; `attrs`/`invisible` de v11; `.po` solo con lo nuevo; cadenas en
inglés con `_()`/`_t()` y su entrada en `es.po`.

## 26. Cron, colas y reintentos

**Qué se ve**: método de cron sin `<record model="ir.cron">`; `retry_pattern`
con `FailedJobError`; `identity_key` para deduplicar; `commit()` en un job.

**Por qué importa**: en !2272 el cron no está registrado y nunca se ejecuta; en
!2367 el `retry_pattern` no reintenta porque todo lanza `FailedJobError`; en
!2382 el `identity_key` solo deduplica `PENDING`/`ENQUEUED` y un job `STARTED`
se puede duplicar.

**Corrección**: registra el cron; usa `RetryableJobError` para lo que debe
reintentar, `FailedJobError` para lo que no y `NothingToDoJob` para lo que ya
está hecho; añade un guard de estado (`running`) antes de encolar; no hagas
`commit()` dentro del job.

## 27. Seguridad de datos y solo lectura

**Qué se ve**: un endpoint que promete solo lectura pero ejecuta acciones de
servidor; un token que puede leer `ir.config_parameter`; un `sudo()` que salta
la ACL; una exportación que manda datos personales al proveedor del modelo.

**Por qué importa**: en !2462 el `SET TRANSACTION READ ONLY` se cierra con un
`commit()` dentro de la acción; un token de `base.group_system` lee credenciales;
la ACL decide quién puede ver un dato, pero no qué datos tiene sentido mandar a
un agente.

**Corrección**: separa las tools de lectura de las que escriben; rechaza
tokens de administrador; bloquea modelos sensibles; acota por token; registra
los rechazos; no devuelvas nombres de registros que el usuario no puede leer.

## 28. Proceso: commits, descripción, hilos y re-review

**Qué se ve**: un commit `fix` o `cambios`; descripción vacía; squash antes del
merge; el autor resuelve los hilos; se pide re-review con la pipeline roja.

**Por qué importa**: en !1900 el MR va a la rama equivocada y sin descripción; en
!2113 hay demasiados commits con nombres que no dicen nada; en !2227 el revisor
pide no resolver los hilos para poder repasarlos; en !2070 el autor los cierra y
el revisor pierde el seguimiento.

**Corrección**: conventional commits, un commit por bloque de corrección,
descripción con contexto e issue, sin squash hasta el merge, hilos abiertos,
re-review con pipeline verde y tabla `punto | commit`.

## 29. Respuesta a un hallazgo que no compartes

**Qué se ve**: el autor responde «esto ya funciona» o «no es de este MR» sin
prueba.

**Por qué importa**: el revisor vuelve a abrir el hilo con la misma observación y
la ronda se alarga.

**Corrección**: responde con `fichero:línea`, un test que lo demuestre o una cita
del core; si el cambio es de otro MR, dilo y enlázalo. Si el revisor se equivoca,
demuéstralo con la misma moneda: línea, reproducción o documento.

## 30. Cuándo parar de corregir

Un MR no se aprueba por acumulación de commits: se aprueba cuando los
bloqueantes están cerrados y la pipeline está verde. Si una ronda nueva descubre
un problema estructural (el diseño no cumple la issue, el alcance es 5 veces el
pedido, la migración no es viable), para y replantea con el revisor antes de
seguir parcheando. En !2272 el revisor terminó recomendando dividir o cancelar el
MR: 14 bloqueantes y un alcance 5-6 veces mayor que la issue no se arreglan con
commits sueltos.

## 31. Dependencia transitiva repetida en el manifiesto

**Qué se ve**: un módulo nuevo declara `connector` y `queue_job` porque importa
`odoo.addons.queue_job`, aunque su dependencia directa ya los trae.

**Por qué importa**: el `depends` se convierte en el cierre del padre; el
revisor lo quita y la ronda se pierde en una discusión de manifiesto.

**Corrección**: declara lo que usas y que el padre no garantiza. Comprueba el
manifiesto del padre; un import transitivo no se declara.

## 32. `or {}` que enmascara el contrato

**Qué se ve**: `values = super(...).gtin_qty(binding) or {}` antes de comprobar
si `values` existe.

**Por qué importa**: oculta un `None` real y convierte un fallo de contrato en
un diccionario vacío silencioso.

**Corrección**: `values = super(...)` y `if not values or "clave" not in values`;
maneja el contrato explícitamente.

## 33. Mezclar `product_uom_qty` con la UdM del producto

**Qué se ve**: una suma de `product_uom_qty` redondeada con
`product_id.uom_id.rounding`.

**Por qué importa**: `product_uom_qty` está en la UdM del movimiento; el
redondeo del producto no le corresponde y el payload puede salir desviado.

**Corrección**: suma `product_qty` (UdM del producto) o convierte con
`_compute_quantity`; redondea siempre en la UdM correcta.

## 34. Comentario que repite el código o el README

**Qué se ve**: `# gtin -> (cantidad, unidad)` o un párrafo que ya está en el
README.

**Por qué importa**: el revisor lo quita; el código y el README son la fuente.

**Corrección**: cero comentarios de prosa en código nuevo o modificado;
docstrings, `help` y README son documentación. Cabeceras legales y directivas de
herramienta no cuentan.

## 35. Test acoplado a `run()` o a un método interno

**Qué se ve**: un test que parchea `run()` o usa `assert_called` para comprobar
la implementación.

**Por qué importa**: falla con cualquier refactor del conector y no prueba la
regla de negocio; el revisor lo quita y pide el test de comportamiento.

**Corrección**: prueba el efecto observable (movimientos, cantidades, estado,
mensaje); mockea solo HTTP/cola/reloj en la frontera. Si el comportamiento ya
está cubierto, el test de implementación se puede quitar y se dice en el MR.

## 36. Retry infinito en un estado terminal

**Qué se ve**: un `RetryableJobError` cuando todos los movimientos del producto
están cancelados y `force_assign_pickings` está desactivado.

**Por qué importa**: el job se reintenta sin fin y el albarán queda parado; no es
un fallo transitorio.

**Corrección**: distingue «no hay movimientos» (puede ser transitorio) de «hay
movimientos y todos están cancelados» (terminal). En el terminal: `warning` +
`message_post` + `continue` o `NothingToDoJob`; en el transitorio:
`RetryableJobError`.

## 37. Limitación conocida escondida en un comentario

**Qué se ve**: una desviación del conector se explica solo con un comentario en
el código.

**Por qué importa**: el revisor pide que la limitación esté en el README y en la
descripción del MR; el comentario no sobrevive a la siguiente edición.

**Corrección**: documenta la limitación en README y MR, con el motivo y el
alcance; el código queda limpio.

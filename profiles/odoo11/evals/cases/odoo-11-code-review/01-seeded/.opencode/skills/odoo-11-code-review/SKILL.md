---
name: odoo-11-code-review
description: "Revisar módulos Odoo 11 antes de commit o PR."
version: 1.2.1
author: Skippy (Nicolás Ramos)
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [odoo, odoo11, review, calidad, checklist]
    category: software-development
    related_skills: [odoo-11-standards, odoo-11-orm-performance, requesting-code-review]
---

# Revisión de código Odoo 11

## Cuándo usar

Antes de commitear o abrir un PR sobre un módulo Odoo 11; al heredar código de
otro; al revisar lo que ha generado un agente. La regla del cliente es que nada
entra sin evidencia: esto produce esa evidencia.

## Cómo se revisa

1. Leer el diff completo, no solo los ficheros que «parecen» importantes.
2. Ejecutar la batería: `pre-commit run --files <cambiados>`.
3. Levantar y actualizar el módulo: `odoo-bin -u <modulo> --stop-after-init` y leer
   el log entero (en v11 un error de vista no tumba el proceso, deja la vista a medias).
4. Probar el comportamiento real: test automático o reproducción manual con su salida.

Si un paso no se ha ejecutado, no se dice «revisado».

### Verificar lo que te cuentan antes de contarlo

Un informe de revisión, un borrador o un resumen de sesión pueden afirmar que un
arreglo está aplicado o que existe un commit concreto. **Eso no es evidencia.**
Antes de reportarlo: `git log --oneline -n 5`, `git cat-file -t <sha>` (falla con
`Not a valid object name` si el commit no existe) y `git status` para ver si hay
cambios sin commitear. Un commit inventado en un resumen se detecta en dos
segundos y arrastra toda la credibilidad del parte si se repite al usuario.

Lo mismo con las cifras: cada número del parte se reproduce con la consulta o el
comando que lo produjo, o se etiqueta como estimación.

### Cambios que tocan datos o esquema

No se empieza por el índice ni por el borrado. El orden es: **arreglar el código y
sus tests → deduplicar los datos → desplegar el módulo → crear el índice** (con
`CONCURRENTLY`, fuera de transacción). Si el índice va antes que el código que
captura el `IntegrityError`, los procesos que crean la fila en paralelo empiezan a
romper. Antes de borrar nada: enumerar las claves foráneas con `pg_constraint`
(una `ON DELETE CASCADE` borra sin avisar), dejar tabla de respaldo y mapa
`viejo → nuevo` para poder revertir, y ejecutar con cron y colas parados. Receta
con SQL: `odoo-11-orm-performance`, `references/deduplicacion-e-indices-unicos.md`.

### Función implementada pero dormida

Un campo de configuración nuevo —y sobre todo un tri-estado— **no cambia el
comportamiento hasta que alguien lo escribe**. Antes de afirmar que una función
está activa, se cuenta por modelo en la base:

```sql
select count(*) from stock_location where fix_stock_quant is not null;
```

Si devuelve 0 con el código desplegado, la lógica está viva pero **muerta de
hambre**: lo que falta es la configuración, no el desarrollo, y decirlo así evita
que se planifique otra vez lo ya hecho. Vale para interruptores globales,
selecciones de tres estados y cualquier campo que module una ruta de código.

- Se revisa también el **valor por defecto del interruptor global**: si viene
  activo, basta con que la migración marque un solo registro para que la función
  entre en producción en ese momento. Ese riesgo se escribe en el parte y se
  despliega con el interruptor apagado, activándolo después de probar.
- El campo existe en varios modelos a la vez (regla, ubicación, tipo de
  operación): se cuentan **todos**, porque uno solo configurado ya cambia el
  resultado de los movimientos que lo usan.

## Checklist

### Compatibilidad v11

- [ ] `__manifest__.py` (no `__openerp__.py`), versión `11.0.x.y.z`
- [ ] Raíz XML `<odoo>`
- [ ] Visibilidad con `attrs=`, sin `invisible="expresión"`
- [ ] Sin f-strings ni sintaxis 3.6+ (vermin `-t=3.5-`)
- [ ] `create()` recibe un dict, no una lista
- [ ] Assets en `views/assets.xml`, no en el manifiesto
- [ ] Sin `models.Constraint` (v12+); en v11 la unicidad va en `_sql_constraints`
- [ ] Sin `type="workflow"` en botones

### Modelo

- [ ] `_description` presente en cada modelo
- [ ] `@api.multi` donde se itera; sin `@api.one` nuevo
- [ ] Campos calculados que se filtran u ordenan: `store=True`
- [ ] Relaciones con `ondelete` explícito cuando importa la integridad
- [ ] `_sql_constraints` donde haya unicidad real

### Vistas

- [ ] Todo campo usado en `attrs` está declarado en la vista
- [ ] Herencia por xmlid, no por id de base de datos
- [ ] `position="replace"` justificado
- [ ] Sin tocar el core de Odoo

### Seguridad

- [ ] `ir.model.access.csv` para cada modelo nuevo
- [ ] Reglas `ir.rule` para lo que un dominio de vista no protege
- [ ] `sudo()` justificado en comentario y sin bucles alrededor
- [ ] Sin credenciales, tokens ni datos de cliente en el código
- [ ] Campos con credenciales (`password`, `token`, `secret`, `*_key`,
      `*_passphrase`, `oauth*`) con `groups` y ACL de lectura de
      administrador; los modelos de configuración de integraciones
      (`*.config`, `*.backend`, `*.webhook`) se revisan enteros
- [ ] Campos derivados que copian una credencial (base64, hash, refresh)
      cuentan igual que el original: `bpost_passphrase_encoded` no tenía
      `groups` y `bpost_password` sí
- [ ] Repasa el árbol, no solo el diff: `python3
      ../factorlibre-mr-preflight/scripts/scan_secret_fields.py --root
      odoo/custom/src`. La interfaz y XML-RPC usan la misma ACL; el conector
      que filtre por nombre no tapa la fuga. Detalle y checklist: skill
      `odoo-11-credential-security`

### Rendimiento

- [ ] Sin `search` dentro de bucles (N+1)
- [ ] `@api.one` con un `search` dentro cuenta como N+1: se ejecuta una consulta por registro; pásalo a `@api.multi` y agrega con `read_group`
- [ ] Agregados con `read_group`, no sumando en Python
- [ ] `search_read` con `fields` y `limit` cuando solo se lee
- [ ] Índices en campos de filtrado frecuente
- [ ] Escrituras en bloque sobre el recordset

### Datos

- [ ] Datos que el cliente puede editar con `<data noupdate="1">`
- [ ] Secuencias, plantillas de correo y parámetros: `noupdate="1"`
- [ ] Orden de `data` en el manifiesto respeta dependencias

### Pruebas

- [ ] Test que falla sin el cambio y pasa con él
- [ ] `--test-enable` ejecutado, no supuesto
- [ ] Log sin WARNING/ERROR del módulo tras `-u`
- [ ] Los datos de prueba cumplen las constraints que el CI tiene cargadas de
      verdad (código de barras válido, `default_code` escrito en la plantilla): la
      base de desarrollo no tiene los mismos módulos que el job, así que un test
      verde en local puede ser rojo en la pipeline por el entorno, no por el cambio

### Documentación

- [ ] Cada campo nuevo o modificado tiene `help=` relleno (regla del cliente, ver
      `odoo-11-standards`). Sin `help`: no pasa revisión.
- [ ] En el parte se enumera **cada** campo sin `help=`, uno a uno; no vale un
      «faltan help» genérico
- [ ] El `help` dice qué representa, unidad o formato y efecto en el proceso; no
      repite el `string` ni es un copia-pega del campo de al lado
- [ ] Si cambió el comportamiento de un campo, su `help` está actualizado en el
      mismo commit
- [ ] Docstring en los métodos públicos y comentario donde la lógica no se deduce
- [ ] `README.rst` describe qué hace y qué hereda

## Cómo revisa FactorLibre estos repos

La checklist vinculante está en `.gitlab/merge_request_templates/MR.md` del propio
repo. Antes de abrir un MR contra sus repos, recórrela tú: funcionalidad frente a
los requisitos numerados de la issue, nombres de funciones y variables (guía OCA:
el recordset es `partner`, no `partner_id`), diseño y complejidad, tests, `depends`
del manifiesto, README del módulo, mensaje de commit y descripción del MR, y la
versión `11.0.x.y.z` (x si hay cambio de modelo o vistas que pueda requerir
migración, y si el cambio exige actualizar el módulo, z si no).

Del manifiesto: todo modelo o vista heredada necesita su módulo en `depends`. Un
`depends` incompleto no falla con el juego completo instalado y revienta con
`External ID not found` al instalar el módulo solo, que es justo lo que hace el CI.

Correcciones en commits nuevos y sin squash hasta el merge, para que la segunda
revisión sea incremental. Los hilos abiertos los cierra el revisor; el autor solo
si está resuelto del todo y es evidente.

Su veredicto va en dos capas: hilos en la línea exacta del diff (`file:line`) y un
informe general con cabecera (MR, issue, SHA del commit revisado) más tabla de
resumen (tier, ficheros, líneas, pipeline con id de job, bots, tests, % de
cumplimiento de la issue) y severidades numeradas 🔴 bloqueante / 🟡 importante /
🔵 sugerencia. En rondas siguientes exigen tabla de estado por hallazgo con el SHA
de cada corrección.

Bloquean siempre: código comentado que llega a master, tests desactivados o no
importados para poner el CI en verde, migración ausente al renombrar claves de
configuración persistidas, cascadas de borrado sin log ni dry-run, y reimplementar
a mano cálculos del core (`compute_all`, `_amount_all`) en vez de usar la opción
nativa de Odoo.

Al devolver una revisión de este código, replica esa forma: cita `fichero:línea`,
reproduce el fallo con importes o cantidades concretas, cita el core por
`ruta:línea` y propón la vía nativa antes que el override. Para leer sus MRs,
issues y el patrón completo, `gitlab` (`references/review-conventions.md`).

Para el checklist operativo completo, el catálogo de patrones con ejemplos y el
script de preflight que se ejecuta antes de abrir el MR, usa
`factorlibre-mr-preflight`; esta sección es solo el resumen.

## Segunda opinión con otro modelo

Una pasada de otro modelo sobre el mismo diff encuentra fallos que la checklist
no ve, pero solo si se le ata a la versión. Lanzamiento que funciona, en solo
lectura (sin poder escribir ni ejecutar nada):

```bash
<reviewer-cli> --model <approved-model> -p "<encargo>" \
  --allowedTools "Read,Grep,Glob,Bash(git log:*),Bash(git diff:*)" \
  > /tmp/revision.md 2>&1
```

> El CLI y el modelo aprobados se configuran fuera del repo. No se escriben en
> este documento ni en los informes; aquí solo se describe el encargo.

- **El encargo nombra la versión y el núcleo, y exige cita.** «Es Odoo 11; el
  núcleo está en `<ruta>`; antes de proponer cualquier API, cita `archivo:línea`
  del núcleo que demuestre que existe en v11; no propongas nada de v12 o
  posterior». Sin esa frase el revisor recomienda APIs modernas y hay que
  descartar media revisión.
- **Se escribe a fichero y se lee entero.** Si se canaliza la salida por un
  filtro que muestre solo el final, se pierde el principio del informe, que es
  donde van los bloqueantes.
- **Cada hallazgo se comprueba contra el núcleo antes de arreglarlo.** El revisor
  también se equivoca con la versión: una primera pasada aseguró que
  `check_field_access_rights` no existía en v11, y sí está (`odoo/models.py`,
  invocado desde `read()`); la siguiente lo corrigió al leer el core. Una
  búsqueda del símbolo en el árbol del núcleo decide en segundos quién tiene
  razón.
- **Un bloqueante puede estar ya arreglado.** El revisor trabaja sobre el dossier o
  el commit que se le pasó, no sobre HEAD: antes de tocar nada se mira el fichero
  citado en la línea citada. Si el código ya lo cubre, se descarta el hallazgo con
  la prueba delante en vez de «arreglarlo» otra vez o, peor, de darlo por bueno sin
  mirar.
- **Cada hallazgo se clasifica antes de tocarlo: nuevo, ya cerrado o falso.** Los
  informes sobre una copia a medio editar traen hallazgos de código que ya no
existe: el revisor lee el árbol mientras se está cambiando y describe el estado
  intermedio. Se revisa contra el commit, se dice cuál, y lo que no aguanta se
  descarta con la línea delante.
- **La tercera pasada existe y encuentra cosas nuevas.** Dos rondas no son el techo:
  la segunda encuentra los falsos verdes de los tests y las frases que la
  documentación promete y el código no cumple, y una tercera sobre los arreglos
  destapa los fallos introducidos al arreglar (un valor que se cuela, una rama que
  se queda sin tope, una excepción nueva en un camino que antes no se ejecutaba).
  En un módulo con superficie de seguridad (autenticación, transacción de solo
  lectura, límites) cuatro y cinco rondas han seguido devolviendo cosas reales. La
  revisión se para cuando una pasada no devuelve nada bloqueante, no cuando el
  revisor se queda sin ideas ni cuando el autor se cansa.
- **Citar el núcleo bien no garantiza acertar la consecuencia.** Un informe puede
  citar la línea correcta de `odoo/http.py` y equivocarse en lo que implica; pasó
  con «la transacción de la petición se confirma siempre, así que la conexión
  propia sobra», que era plausible y falso en la práctica. Cuando el hallazgo
  propone **quitar** una protección, no se quita porque el razonamiento encaje:
  se monta el caso y se mira qué queda en la base. El que decide es el
  comportamiento, no la cita.
- **La ronda siguiente recibe una respuesta numerada, bloqueante por bloqueante**
  (qué se hizo y en qué fichero o commit). Es lo que convierte un «apto con
  condiciones» en «apto»; devolver un párrafo genérico obliga a otra ronda.
- **El encargo de una ronda de arreglos pide explícitamente dos cosas**: revisar si
  los arreglos de la última tanda son correctos de verdad (leyéndolos, no fiándose
  del resumen) y buscar regresiones introducidas por ellos. Sin esas dos frases el
  revisor vuelve a recorrer el módulo entero y repite hallazgos ya cerrados.
- **Antes de una ronda, el árbol se commitea.** Si se lanza sobre cambios sin
  commitear, el revisor ve un estado intermedio y el informe mezcla lo que hay con
  lo que había.
- **Las rondas siguientes revisan los arreglos, no el módulo entero**, y se le
  pide cazar «formas de leer un campo restringido sin tener el grupo». Así
  aparecieron los agregados de `read_group` y el dominio con dos negaciones.
- **Comprobar qué modelo contestó de verdad.** El CLI puede usar un modelo por
  defecto distinto del que crees: fija el aprobado con su flag y, si la salida es
  JSON, lee el identificador canónico (`modelUsage`/`canonicalModel`) antes de
  reportar. Ese identificador se guarda en el registro interno; no se publica.
- Su veredicto no sustituye la prueba: los tests y la reproducción real siguen
  siendo la evidencia que se entrega.
- **El modelo que revisa no se publica.** Informes, comentarios de ticket,
  changelogs y documentación hablan de «revisión externa» o «revisión
  independiente», nunca del modelo ni del CLI usado. Vale para los documentos que
  se entregan al cliente y para lo que se pega en Jira.
- **Cada ronda se le pasa solo lo que cambió** (commits, ficheros, medidas) y se
  le pide veredicto sobre eso; una revisión completa se reserva para el cierre y
  para cuando cambia el diseño, no para cada arreglo.
- **Un bloqueante se cierra con código o con dato, no con una opinión.** Si el
  revisor pide unicidad en base de datos, primero se comprueba si ya hay
  duplicados y cuántos; si los hay, el índice no se puede crear sin deduplicar y
  eso cambia el plan y el orden de despliegue.

## Cuando avisan de «comentarios nuevos» en el MR

Antes de ponerse a trabajar: comprobar que son nuevos. Los hilos se leen por API y se comparan
con la fecha del último commit propio.

```bash
curl -s -H "PRIVATE-TOKEN: $TOKEN" \
  "https://<host>/api/v4/projects/<grupo>%2F<repo>/merge_requests/<iid>/discussions?per_page=100" \
  | python3 -c "import json,sys; [print(n['created_at'], n['author']['username'], (n['body'] or '')[:60]) for t in json.load(sys.stdin) for n in t['notes'] if not n['system']]"
```

- Si todos los `created_at` son anteriores al commit que cierra esos puntos, **no hay nada nuevo**
  y la respuesta lo dice con las fechas delante en vez de reabrir el trabajo.
- El aviso de «hay comentarios nuevos» muchas veces es el propio push recién hecho: el MR cambia
  de `updated_at` y la plataforma lo pinta como actividad, sin que nadie haya escrito.
- Los hilos ya cerrados en código se contestan uno a uno con el commit que los cierra; volver a
  tocarlos sin decirlo es lo que hace que el revisor repita la observación.

## Salida de la revisión

Un parte corto, con evidencia:

```
QUÉ: <una frase>
PRUEBA: <comando y su salida, o fichero y ruta>
RIESGO: verde | ámbar (preparado sin verificar) | rojo (bloqueado, motivo)
QUEDA: <o «nada»>
```

Nunca se pinta verde lo que no se ha ejecutado. Si algo no se pudo verificar, se
dice.

## Contrato del parte

- Cada hallazgo va como `fichero:línea: SEVERIDAD: qué pasa y cómo se arregla`.
- Si el fichero no existe (ACL, README, JS), cita el punto donde debería
  declararse (`__manifest__.py:<línea>`), no `directorio:1`.
- Enumera los campos sin `help=` uno a uno; no los agrupes en una frase.
- No llames «inyección SQL» a una interpolación con un entero: di «SQL crudo
  interpolado» y explica el riesgo real (sin ACL, sin `unlink`, sin cascada).
- Propón solo APIs de v11: `_sql_constraints`, no `models.Constraint`; `attrs=`,
  no `invisible="..."`; `type="object"`, no `workflow`.
- Si no has ejecutado `-u`, `--test-enable` o `pre-commit`, el `RIESGO` es ámbar
  y lo dices.

## Errores que esta checklist evita

| Síntoma | Causa real |
|---|---|
| Vista que no cambia | falta `-u`, o el XML no está en `data` |
| `Field 'x' does not exist` | campo declarado, módulo sin actualizar |
| Botón que no hace nada | método sin `@api.multi`, o acción mal referenciada |
| Campo calculado vacío | falta `store=True` o la dependencia |
| `AccessError` con admin | regla global de registro, no ACL |
| JS que no carga y sin error | assets declarados en el manifiesto |
| `_sql_constraints` sin efecto | requiere `-u` |
| `models.Constraint` en v11 | no existe; usa `_sql_constraints` |

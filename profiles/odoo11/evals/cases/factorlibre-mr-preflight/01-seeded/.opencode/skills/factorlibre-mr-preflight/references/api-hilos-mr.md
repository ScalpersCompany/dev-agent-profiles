# API de hilos de un MR (GitLab autohospedado)

Receta para leer, contestar y resolver los hilos de una merge request sin abrir
el navegador. Sustituye `<host>`, `<proyecto>` (`grupo%2Frepo`, con la barra
codificada) y `<iid>`.

## Autenticación y scopes

```bash
TOKEN=$(grep "<usuario>" ~/.git-credentials | sed -E 's#https://[^:]+:([^@]+)@.*#\1#' | head -1)
curl -s --header "PRIVATE-TOKEN: $TOKEN" https://<host>/api/v4/personal_access_tokens/self | head -c 400
```

`scopes` decide qué se puede hacer:

- `read_api` (+ `write_repository` para git): leer MRs, diffs e hilos. Escribir
  comentarios o resolver devuelve `403 insufficient_scope` con
  `{"error":"insufficient_scope", ...}` y no publica nada.
- `api`: lectura y escritura. Necesario para `POST .../notes` y
  `PUT .../discussions/<id>?resolved=true`.

## Encontrar los hilos abiertos

```bash
# MRs abiertas de todo lo visible, con el indicador de bloqueo
curl -s --header "PRIVATE-TOKEN: $TOKEN" \
  "https://<host>/api/v4/merge_requests?scope=all&state=opened&per_page=100"

# Detalle de una MR: rama, pipeline, merge_status, blocking_discussions_resolved
curl -s --header "PRIVATE-TOKEN: $TOKEN" \
  "https://<host>/api/v4/projects/<proyecto>/merge_requests/<iid>"
```

`blocking_discussions_resolved: false` solo dice que hay algo sin resolver, no
cuántos hilos ni si siguen vivos: hay que leer las discusiones.

```bash
curl -s --header "PRIVATE-TOKEN: $TOKEN" \
  "https://<host>/api/v4/projects/<proyecto>/merge_requests/<iid>/discussions?per_page=100" \
  > /tmp/discussions.json
```

Filtra en Python, no a ojo:

```python
import json
for disc in json.load(open('/tmp/discussions.json')):
    ns = [n for n in disc['notes'] if not n.get('system')]      # fuera eventos
    if not ns or not ns[0].get('resolvable') or ns[0].get('resolved'):
        continue
    n = ns[0]
    pos = n.get('position') or {}
    print(n['created_at'][:16], pos.get('new_path'), pos.get('new_line') or pos.get('old_line'))
    print(' ', n['body'][:200])
```

Dos trampas de esos datos:

- La mayoría de las entradas son `system: True` (commits añadidos, asignaciones).
  Sin filtrarlas parece que la MR tiene hilos que no existen.
- `position.new_line` es la línea en la versión del diff que se comentó, no en
  HEAD. Para citar en la respuesta, busca la línea actual en el fichero.

## Contestar y resolver

```bash
# responder dentro del hilo (no crea uno nuevo)
curl -s -X POST --header "PRIVATE-TOKEN: $TOKEN" \
  --data-urlencode "body=<texto>" \
  "https://<host>/api/v4/projects/<proyecto>/merge_requests/<iid>/discussions/<discussion_id>/notes"

# marcar el hilo como resuelto
curl -s -X PUT --header "PRIVATE-TOKEN: $TOKEN" \
  "https://<host>/api/v4/projects/<proyecto>/merge_requests/<iid>/discussions/<discussion_id>?resolved=true"
```

`<discussion_id>` es el campo `id` de la discusión (40 hex), no el de la nota.
Un script que itere las discusiones abiertas y haga las dos llamadas por hilo, en
orden, evita erratas; guarda antes los ids en JSON para poder repetir sin
recalcular.

## Verificar después

- Vuelve a pedir las discusiones y cuenta las que siguen abiertas: es la única
  prueba de que el `resolve` entró.
- `403` en el `POST`: scopes del token (arriba). `404`: `discussion_id` de una
  nota en vez de una discusión, o `iid` de otro proyecto.
- El pipeline del `head_pipeline` en `success` sobre el SHA de HEAD es la prueba
  de que los tests del MR pasan; si el SHA del pipeline no es el de HEAD, está
  desactualizado.

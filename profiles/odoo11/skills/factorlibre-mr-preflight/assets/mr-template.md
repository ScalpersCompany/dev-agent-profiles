# Plantilla de descripción de MR

> Copia desde aquí. No dejes ninguna sección vacía: si no aplica, escribe
> «No aplica» y por qué. La descripción es lo primero que lee el revisor y una
> descripción vacía ya es un hallazgo.

## Título

`[TIPO] modulo: resumen en una línea`

Tipos: `[ADD]` módulo o funcionalidad nueva, `[IMP]` mejora, `[FIX]` corrección,
`[REF]` refactor sin cambio funcional, `[REM]` eliminación, `[MIG]` migración.

## Issue / tarea

- Issue: `odoo-11/scalpers-v11#<iid>` (o el repo que corresponda)
- Tarea de Jira: `SIS-<id>` si existe
- Work item de GitLab: `<iid>` si el flujo lo usa

## Qué cambia y por qué

- Contexto: qué pasaba antes, con un caso real (pedido, tienda, importe, fecha).
- Causa: por qué pasaba.
- Solución: qué hace este MR y por qué esta vía y no otra.
- Alcance: qué incluye y qué deja fuera. Si hay refactor, dilo.

## Requisitos que cubre

| Requisito de la issue | Estado | Dónde se prueba |
|---|---|---|
| R1 | ✅ | `test_01_...` |
| R2 | ✅ | validación en TEST |

## Cómo se ha probado

- Base: `<base>` / TEST / PRE, con los módulos `<modulos>`.
- Comando: `odoo -d <base> -i <modulos> --test-enable --stop-after-init`
- Resultado: `Ran N tests ... OK` (pega la línea, no la resumas).
- Prueba funcional: pasos, datos y resultado observado.
- Capturas o vídeo si es UI/POS.

## Migración y datos

- ¿Hay migración? `<migrations/11.0.x.y.z/...>` o «No aplica».
- ¿Se renombra o borra un campo persistido? Sí/No. Si sí, migración y prueba en
  instalación nueva y en actualización.
- ¿Hay carga inicial? `post_init_hook` (no `migrations/11.0.1.0.0/`).
- ¿Se tocan datos existentes? Cuántos, cómo se identifican, cómo se revierte.

## Despliegue

- Módulos a actualizar, en orden: `-u mod_a,mod_b`.
- ¿Hay que parar cron/colas? ¿Hay que ejecutar un script? ¿Hay que configurar
  algo antes o después?
- Dependencias externas: versión de librería, endpoint, credencial, migración de
  otro repo.
- Rollback: qué se hace si falla.

## Checklist

- [ ] Rebase sobre `origin/master`; sin conflictos.
- [ ] `preflight_mr.py` sin `ERROR`.
- [ ] `pre-commit run --files <cambiados>` limpio.
- [ ] Tests en base con el closure de `depends`, no en la base completa.
- [ ] Versión del manifest subida según el cambio.
- [ ] `depends` completo; sin dependencias redundantes.
- [ ] `help` en campos nuevos/modificados; README/HISTORY si cambia el
      comportamiento.
- [ ] Migración si se renombra o borra algo persistido; idempotente.
- [ ] ACL/`ir.rule` para modelos nuevos, incluidos `TransientModel`.
- [ ] Sin tests desactivados, código comentado, `print`, `console.log` ni
      secretos.
- [ ] Descripción del MR con issue, caso real y evidencia.

## Riesgos y notas para el revisor

- Qué parte del diff quieres que mire con más atención.
- Qué decisión tomaste y por qué (alternativas descartadas).
- Qué queda pendiente para otro MR y por qué no va aquí.

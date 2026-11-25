# Metodología Scalpers aplicada a un microservicio

Esta skill no sustituye la metodología corporativa: la consume. Antes de diseñar, lee la regla de
entrada de `~/.agents/AGENTS.md` y la versión de la metodología atada al proyecto (el HTML
autocontenido del workspace o, si no existe, la fuente de `scalpers-tech-doc`). Si una práctica de
esta skill contradice esa base, gana la base documental.

## Qué cubre la skill y qué no

| Fase / artefacto | Esta skill | Dónde vive la fuente |
|---|---|---|
| Descubrimiento, personas, journey, UX | No | Metodología, PRD y flujos de producto |
| PRD, historias de usuario, criterios de aceptación | No los redacta | Plantillas de la metodología y `_doc` del servicio |
| ADR de arquitectura y decisiones | Sí, como consumidora | Plantilla ADR de la metodología |
| Especificación de API y contrato | Sí | `contracts/` y plantilla de API spec |
| Implementación DDD / hexagonal / SOLID | Sí | SDLC de la metodología y esta skill |
| TDD, contract testing, E2E | Sí | SDLC y plan del proyecto |
| GitFlow, tags, entornos y releases | Sí, con la excepción de piloto | `gitflow_es.md` y `git-repositories.md` |
| Documentación MyST e índices | Sí, como regla de entrega | Libro de metodología y `_doc` |
| Stack aprobado | Sí, como referencia | `development/tech-stack.md` |
| Roles, estimación, DoR/DoD | No los redefine | Metodología y gestión de proyectos |

## Reglas de la empresa que la skill hace suyas

- Producción no se toca sin autorización explícita para esa acción concreta.
- Nada se declara hecho sin evidencia: comando, test, `diff`, respuesta HTTP o fichero releído.
- Todo desarrollo se prueba de extremo a extremo y demuestra que no rompe lo anterior.
- Nada destructivo sin permiso; antes de borrar, renombrar a `.bak-<fecha>`.
- Commits convencionales, firmados y sin atribución a IA ni `Co-Authored-By`.
- Dos fallos del mismo intento implican cambio de enfoque o parada.
- Documentación en español; código, identificadores y especificaciones de API en inglés.
- Changelog obligatorio en el mismo commit que el cambio.
- Sin comentarios de prosa en código nuevo o modificado; solo directivas y cabeceras legales.

## GitFlow y entornos

- `main` es producción estable; `devel` integra evolutivos; `feature/*` nace de `main`;
  `release/*` prepara versión; `hotfix/*` corrige producción.
- Tags de integración `dev-YYYYMMDD`; versión `vX.Y.Z`; `demo-vX.Y.Z` y `prod-vX.Y.Z`.
- CI/CD: dev automático desde `devel`/`dev-*`; staging automático desde `main`/`v*`; producción
  manual con aprobación.
- **Excepción de piloto acordada:** un solo repo con los microservicios en `services/<nombre>/` y
  un compose raíz; no se crean `_doc`, `_test` ni `_infra` para el piloto. La separación por repos
  de la metodología se aplica al pasar a plataforma.
- El módulo puente de Odoo es un módulo Odoo en `scalpers-v11`; no es un servicio del repo del
  piloto ni se mezcla con sus transacciones.

## Documentación y contrato

- Markdown MyST dentro de `source/content/`; todo fichero nuevo se declara en `index.rst` y
  `myst.yml`.
- Diagramas como código (PlantUML, Mermaid o Wavedrom); captura raster solo de un sistema real.
- Plantillas de ADR, PRD y User Story: no se inventa estructura.
- Sin duplicación: se enlaza la fuente.
- El contrato del servicio es la fuente de verdad y se versiona con SemVer independiente; los
  cambios incompatibles abren ventana de migración.

## Calidad y stack

- DDD, arquitectura hexagonal, SOLID, TDD y contract testing son el marco de implementación.
- Cobertura y umbrales: los que fije el proyecto; el piloto de transporte usa 85 % global y 90 %
  en dominio.
- Stack backend aprobado: Python, uv, pytest, FastAPI, Pydantic, OpenTelemetry, PostgreSQL.
- Observabilidad: Prometheus/Grafana/Loki/Tempo o Datadog; edge APISIX/Coraza/Traffic Server
  cuando haya exposición; Keycloak/Casbin para usuarios y API key entre servicios.
- Seguridad: secretos por entorno o vault, nunca en repositorio, logs ni respuestas.

## Entrega

- Un cambio, un commit; tests y documentación en el mismo commit que el comportamiento.
- `CHANGELOG.md` con versión y fecha; README con caso de uso, configuración y pruebas.
- Merge Request con pipeline en verde; producción con aprobación explícita.
- Declarar el riesgo (`Risk: item N` o `Risk: none`) y las pruebas observadas.

## Referencias locales

- `~/.agents/AGENTS.md` — regla de entrada y normas de artefactos.
- `scalpers-tech-doc/books/scalpers-methodology/` — metodología, SDLC, GitFlow y stack.
- `scalpers-tech-doc/books/scalpers-opsdoc/` — proceso de negocio y modelo de datos.
- `references/architecture.md` — implementación técnica de esta skill.
- `references/checklist.md` — puerta de entrega.

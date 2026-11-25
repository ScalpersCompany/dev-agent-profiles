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

## Reglas que la skill no reescribe

- La norma de empresa y la metodología mandan; esta skill no las copia ni las resume.
- Los artefactos de producto (PRD, historias, roles, DoR/DoD, estimación) viven en la metodología.
- GitFlow, tags, entornos, CI/CD, stack aprobado y estructura documental se consultan en la fuente;
  la skill solo enlaza.
- La excepción de piloto está en `AGENTS.fragment.md` y en esta referencia: un repo con
  `services/<nombre>/` y compose raíz; los repos separados se aplican al pasar a plataforma.
- Las integraciones con sistemas existentes son adaptadores o módulos separados; no son carpetas
  de servicio ni comparten transacciones con el microservicio.

## Cobertura y calidad

El proyecto fija sus umbrales. Si no hay decisión, la referencia es 85 % global y 90 % en dominio.
La skill no sustituye el plan de pruebas del proyecto ni sus criterios de aceptación.

## Referencias locales

- `~/.agents/AGENTS.md` — regla de entrada y normas de artefactos.
- `scalpers-tech-doc/books/scalpers-methodology/` — metodología, SDLC, GitFlow y stack.
- `scalpers-tech-doc/books/scalpers-opsdoc/` — proceso de negocio y modelo de datos.
- `references/architecture.md` — implementación técnica de esta skill.
- `references/checklist.md` — puerta de entrega.

# Changelog

## [1.3.1] - 2026-11-18

### Changed

- La skill documenta la compatibilidad con Hermes, OpenCode y Claude Code: mismo
  `SKILL.md`, scripts Python 3.8+ y el gate de comentarios en un hook de git, sin API
  específica de agente.

## [1.3.0] - 2026-11-18

### Added

- Revisión de la lógica de FactorLibre en el MR del conector IDCloud (7 hilos):
  dependencia transitiva, `or {}`, UdM `product_qty`/`product_uom_qty`, comentarios,
  test acoplado, retry terminal y limitación documentada.
- `preflight_mr.py`: comprueba comentarios de prosa en líneas añadidas, `or {}`,
  `product_uom_qty` con redondeo, tests que parchean `run()`, `RetryableJobError`
  junto a movimientos cancelados y `depends` transitivas cuando el padre está en
  el árbol.
- `references/patrones-y-ejemplos.md`: patrones 31-37 con la corrección esperada.

### Changed

- La norma de `depends` pasa de «todo import que se use» a «lo que el padre no
  garantice»: un import de una dependencia transitiva no se declara; el revisor
  quita el cierre del padre. El INFO del preflight ahora pide confirmarlo, no
  añadirlo a ciegas.
- Los tests deben probar comportamiento, no llamadas internas; se puede quitar
  un test de implementación si el comportamiento ya está cubierto, diciéndolo en
  el MR.
- La sección 10 ya no pide «comentario donde la lógica no se deduce»: prohíbe
  comentarios de prosa y deja docstrings, `help` y README como documentación.

### Fixed

- La skill 1.2.0 se contradecía con la norma global 4.1 sobre comentarios.
- El preflight podía empujar a declarar una dependencia que el padre ya trae;
  ahora distingue import transitivo de dependencia directa.

## [1.1.0] - 2026-11-18

### Fixed

- `scan_secret_fields.py` read a single-line field and swallowed the next field,
  so `bpost_passphrase_encoded` disappeared after `api_key`. Every one-line
  field is now its own block.
- `preflight_mr.py` treated the `model="module.model"` attribute of
  `<record>` and `<field>` as an xmlid, producing false
  `xmlidDeOtroModulo` INFO findings for `ir.*` and the module's own models.

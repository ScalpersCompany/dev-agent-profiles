# Changelog

## [1.1.0] - 2026-11-18

### Fixed

- `scan_secret_fields.py` read a single-line field and swallowed the next field,
  so `bpost_passphrase_encoded` disappeared after `api_key`. Every one-line
  field is now its own block.
- `preflight_mr.py` treated the `model="module.model"` attribute of
  `<record>` and `<field>` as an xmlid, producing false
  `xmlidDeOtroModulo` INFO findings for `ir.*` and the module's own models.

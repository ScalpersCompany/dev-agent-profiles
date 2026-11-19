The directory `repo/` is a git fixture for a FactorLibre merge request. It has two branches:

- `master`: the base.
- `feature`: the candidate MR for the new module `addons/broken_loyalty`.

If `repo/` does not exist, create it once with:

```bash
bash setup_repo.sh
```

Do not modify `repo/` after that. Review the MR with the `factorlibre-mr-preflight` skill:

1. Run the skill's preflight:
   `python3 .opencode/skills/factorlibre-mr-preflight/scripts/preflight_mr.py --repo repo --base master --head feature`
2. Run the credential scan:
   `python3 .opencode/skills/factorlibre-mr-preflight/scripts/scan_secret_fields.py --root repo`
3. Walk the rest of the skill's checklist against the diff. The script does not cover ACLs, `help=`, `cr.commit()`, `attrs` fields, manifest assets or migration safety.

Produce the FactorLibre verdict:

- header: MR, issue, branch, HEAD, tier, files, lines, preflight result and exit code;
- one finding per line as `path:line: SEVERITY: rule: what and how to fix`;
- separate the preflight's ERROR/WARN/INFO findings from the checklist findings that the script does not cover;
- quote the preflight summary (N ERROR, N WARN, N INFO) and its exit code;
- end with the skill's `QUÉ / PRUEBA / RIESGO / QUEDA` block.

Do not invent findings; if you cannot verify something, say so. Do not change the repository.

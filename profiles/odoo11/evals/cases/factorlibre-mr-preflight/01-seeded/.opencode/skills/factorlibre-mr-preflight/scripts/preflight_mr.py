#!/usr/bin/env python3
"""Preflight de MR para scalpers-v11 (Odoo 11). Solo lectura.

Uso:
    python3 preflight_mr.py --base origin/master [--head HEAD] [--repo .] [--json]

Salida: ERROR (bloquea), WARN (revisar), INFO (contexto). Codigo 1 si hay ERROR.
No modifica el repositorio, no hace fetch y no ejecuta tests.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"
SEV_ORDER = {ERROR: 0, WARN: 1, INFO: 2}

GENERIC_COMMITS = re.compile(
    r"^(wip|fix|fixes|cambios?|desarrollo|update|updates|merge| merge|arreglos?|"
    r"correcciones?|v\d+|test|tests|pruebas?)$", re.I)


def run(args, repo, check=False):
    p = subprocess.run(args, cwd=str(repo), text=True, capture_output=True)
    if check and p.returncode != 0:
        raise SystemExit("Fallo: %s\n%s" % (" ".join(args), p.stderr.strip()))
    return p


def git(repo, *args):
    return run(["git", *args], repo, check=True).stdout


def changed_files(repo, base, head):
    out = git(repo, "diff", "--name-status", "%s...%s" % (base, head))
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            status, path = parts[0], parts[-1]
            rows.append((status, path))
    return rows


def added_lines(repo, base, head, path):
    """Lineas anadidas del fichero en el rango, con numero de linea nuevo."""
    out = git(repo, "diff", "-U0", "%s...%s" % (base, head), "--", path)
    lines, new_no = [], None
    for raw in out.splitlines():
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
        if m:
            new_no = int(m.group(1))
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            lines.append((new_no, raw[1:]))
            new_no = (new_no + 1) if new_no is not None else None
        elif raw.startswith("-") and not raw.startswith("---"):
            continue
        elif new_no is not None:
            new_no += 1
    return lines


def show_file(repo, ref, path):
    p = run(["git", "show", "%s:%s" % (ref, path)], repo)
    return p.stdout if p.returncode == 0 else None


def parse_manifest(text):
    version = None
    depends = []
    if not text:
        return version, depends
    m = re.search(r"['\"]version['\"]\s*:\s*['\"]([^'\"]+)['\"]", text)
    if m:
        version = m.group(1)
    m = re.search(r"['\"]depends['\"]\s*:\s*\[(.*?)\]", text, re.S)
    if m:
        depends = re.findall(r"['\"]([^'\"]+)['\"]", m.group(1))
    return version, depends


def module_of(path):
    parts = path.split("/")
    if len(parts) > 1 and parts[0] == "addons":
        return parts[1]
    return None


class Finding:
    def __init__(self, sev, path, line, rule, msg):
        self.sev, self.path, self.line, self.rule, self.msg = sev, path, line, rule, msg

    def as_dict(self):
        return {"severity": self.sev, "path": self.path, "line": self.line,
                "rule": self.rule, "message": self.msg}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/master")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    if run(["git", "rev-parse", "--is-inside-work-tree"], repo).returncode != 0:
        raise SystemExit("No es un repositorio git: %s" % repo)
    if run(["git", "rev-parse", "--verify", args.base], repo).returncode != 0:
        raise SystemExit("No existe la base %r; haz git fetch o pasa --base." % args.base)

    findings = []

    def add(sev, path, line, rule, msg):
        findings.append(Finding(sev, path, line, rule, msg))

    # El preflight revisa commits, no el arbol de trabajo
    dirty = run(["git", "status", "--porcelain"], repo).stdout.strip()
    if dirty:
        add(WARN, "(worktree)", 0, "cambiosSinCommitear",
            "Hay cambios sin commitear; el preflight solo revisa commits. Commitea antes de abrir el MR.")

    # Rama y commits
    behind = run(["git", "rev-list", "--count", "%s..%s" % (args.head, args.base)], repo)
    if behind.returncode == 0 and behind.stdout.strip().isdigit():
        n = int(behind.stdout.strip())
        if n > 0:
            add(WARN, "(rama)", 0, "ramaLenta",
                "La rama esta %d commits por detras de %s: rebase antes de abrir el MR." % (n, args.base))
    anc = run(["git", "merge-base", "--is-ancestor", args.base, args.head], repo)
    if anc.returncode != 0:
        add(WARN, "(rama)", 0, "baseNoAncestro",
            "%s no es ancestro de %s: la rama no contiene la base actual." % (args.base, args.head))

    subjects = [s.strip() for s in git(repo, "log", "--format=%s", "%s..%s" % (args.base, args.head)).splitlines() if s.strip()]
    if len(subjects) == 1 and GENERIC_COMMITS.match(subjects[0]):
        add(WARN, "(commits)", 0, "commitGenerico",
            "Un solo commit con mensaje generico (%r): describe que cambia y por que." % subjects[0])
    if len(subjects) > 8:
        add(INFO, "(commits)", 0, "muchosCommits",
            "%d commits en el MR: revisa si se pueden agrupar por modulo antes del merge (sin squash durante la revision)." % len(subjects))

    files = changed_files(repo, args.base, args.head)
    if not files:
        add(INFO, "(diff)", 0, "sinCambios", "No hay cambios entre %s y %s." % (args.base, args.head))
        return emit(findings, args.json)

    # Ficheros que no deberian viajar en el MR
    for status, path in files:
        if path.endswith((".bak", ".orig", ".rej", ".pyc")) or "/__pycache__/" in path:
            add(WARN, path, 0, "ficheroTemporal", "Fichero temporal o de respaldo en el MR: quitalo.")
        if path.startswith("odd/") or path.startswith(".atl/"):
            add(WARN, path, 0, "ficheroAjeno", "Fichero de trabajo del agente en el MR: quitalo.")

    # Tamano del diff
    shortstat = git(repo, "diff", "--shortstat", "%s...%s" % (args.base, args.head)).strip()
    m_add = re.search(r"(\d+) insert", shortstat)
    m_del = re.search(r"(\d+) delet", shortstat)
    total = (int(m_add.group(1)) if m_add else 0) + (int(m_del.group(1)) if m_del else 0)
    if total > 800:
        add(WARN, "(diff)", 0, "diffGrande",
            "El diff tiene ~%d lineas: divide el MR o justifica el alcance." % total)

    modules = sorted({m for _, p in files for m in [module_of(p)] if m})
    changed = {p for _, p in files}

    for mod in modules:
        manifest_path = "addons/%s/__manifest__.py" % mod
        old_manifest = show_file(repo, args.base, manifest_path)
        new_manifest = show_file(repo, args.head, manifest_path)
        old_ver, old_deps = parse_manifest(old_manifest)
        new_ver, new_deps = parse_manifest(new_manifest)
        mod_files = [(s, p) for s, p in files if module_of(p) == mod]
        code_files = [(s, p) for s, p in mod_files if p.endswith((".py", ".xml", ".csv", ".js", ".po", ".less", ".scss"))]

        if new_manifest is None:
            add(ERROR, manifest_path, 0, "manifestAusente",
                "El modulo %s no tiene __manifest__.py en el head." % mod)
            continue

        if code_files and manifest_path not in changed:
            add(WARN, manifest_path, 0, "versionSinBump",
                "Hay cambios de codigo en %s y el manifest no cambia: revisa si toca subir la version." % mod)
        if manifest_path in changed and old_ver == new_ver:
            add(WARN, manifest_path, 0, "versionSinCambio",
                "El manifest de %s cambia pero la version sigue en %s." % (mod, new_ver))

        # Migraciones en la primera version del modulo
        mig = re.findall(r"^addons/%s/migrations/([^/]+)/" % re.escape(mod),
                         "\n".join(p for _, p in mod_files), re.M)
        if mig and new_ver and new_ver.endswith("1.0.0"):
            for v in sorted(set(mig)):
                add(WARN, "addons/%s/migrations/%s" % (mod, v), 0, "migracionEnVersionInicial",
                    "Migracion en la primera version (%s): en una instalacion nueva no se ejecuta. "
                    "Mueve la carga inicial a post_init_hook." % new_ver)

        # Dependencias declaradas vs usadas
        for _, path in code_files:
            for line_no, line in added_lines(repo, args.base, args.head, path):
                for dep in re.findall(r"odoo\.addons\.([a-zA-Z0-9_]+)", line):
                    if dep != mod and dep not in new_deps and dep not in ("base",):
                        add(INFO, path, line_no, "dependenciaUsadaNoDeclarada",
                            "Se importa odoo.addons.%s y no esta en depends de %s." % (dep, mod))
                for xid in re.findall(r"(?:inherit_id|ref|view_id|action|menu|group|template)\s*=\s*[\"']([a-zA-Z0-9_]+)\.", line):
                    if xid != mod and xid not in new_deps and xid not in ("base", "web"):
                        add(INFO, path, line_no, "xmlidDeOtroModulo",
                            "Se referencia el xmlid %s.%s y %s no esta en depends." % (xid, "*", xid))

        # Tests desactivados
        init_path = "addons/%s/tests/__init__.py" % mod
        if init_path in changed:
            for line_no, line in added_lines(repo, args.base, args.head, init_path):
                stripped = line.strip()
                if re.match(r"^#\s*from\s+\.\s+import\s+test_", stripped):
                    add(ERROR, init_path, line_no, "testDesactivado",
                        "Test comentado en tests/__init__.py: no lo desactives para poner el CI en verde.")
            removed = git(repo, "diff", "-U0", "%s...%s" % (args.base, args.head), "--", init_path)
            for raw in removed.splitlines():
                if raw.startswith("-") and not raw.startswith("---") and re.search(r"from\s+\.\s+import\s+test_", raw):
                    add(ERROR, init_path, 0, "testEliminado",
                        "Se elimina un import de test en tests/__init__.py: no lo quites para poner el CI en verde.")

        for _, path in code_files:
            for line_no, line in added_lines(repo, args.base, args.head, path):
                s = line.strip()

                # Debug y peligros
                if re.search(r"\bprint\s*\(", line) and not path.endswith("tests.py"):
                    sev = INFO if "/scripts/" in path else WARN
                    add(sev, path, line_no, "printEnCodigo", "print() en codigo de produccion.")
                if re.search(r"\bpdb\.set_trace\s*\(|\bbreakpoint\s*\(", line):
                    add(ERROR, path, line_no, "debugger", "Debugger en el codigo.")
                if path.endswith(".js") and re.search(r"\bconsole\.log\s*\(|\bdebugger\b", line):
                    add(WARN, path, line_no, "debugJs", "console.log/debugger en JS.")
                if re.search(r"\beval\s*\(|\bexec\s*\(", line) and path.endswith(".py"):
                    add(ERROR, path, line_no, "evalExec", "eval()/exec() en codigo de produccion.")

                # Odoo 11
                if path.endswith(".py"):
                    if re.search(r"@api\.one\b", line):
                        add(ERROR, path, line_no, "apiOne", "@api.one no se usa en codigo nuevo de v11.")
                    if re.search(r"(?<![A-Za-z0-9_])f[\"']", line):
                        add(WARN, path, line_no, "fString", "f-string: revisa que el CI de este repo lo permita (vermin -t=3.5).")
                    if re.search(r"datetime\.now\s*\(", line) and "/models/" in path:
                        add(WARN, path, line_no, "datetimeNow", "datetime.now() es hora del servidor; usa fields.Datetime.now() (UTC).")
                    if re.search(r"raise\s+(UserError|ValidationError)\s*\(\s*[\"']", line):
                        add(INFO, path, line_no, "cadenaSinTraducir", "Mensaje sin _(): no se traducira.")
                    if re.search(r"\.sudo\s*\(\s*\)", line) and "/controllers/" in path:
                        add(WARN, path, line_no, "sudoEnController", "sudo() en controller: justifica el permiso o usa el usuario de la peticion.")
                    if re.search(r"search\s*\(\s*\[\s*\]\s*\)", line) and "limit" not in line:
                        add(WARN, path, line_no, "searchSinDominio", "search([]) sin dominio ni limit: puede recorrer toda la tabla.")
                    if re.search(r"search\s*\([^)]*\)", line) and "limit" not in line and "/models/" in path:
                        add(INFO, path, line_no, "searchSinLimit", "search() sin limit: si esperas un registro, anade limit=1.")

                # XML / vistas
                if path.endswith(".xml"):
                    if re.search(r"\binvisible\s*=\s*[\"'][^\"']*[<>=]", line):
                        add(ERROR, path, line_no, "invisibleExpresion", "invisible con expresion: en v11 usa attrs=.")
                    if re.search(r"\battrs\s*=\s*[\"'][^\"']*\{", line) and "invisible" not in line:
                        pass
                    if re.search(r"\btype\s*=\s*[\"']json[\"']", line):
                        add(ERROR, path, line_no, "tipoJson", "type=json no existe en v11.")

                # JS
                if path.endswith(".js"):
                    if "?." in line:
                        add(WARN, path, line_no, "optionalChaining", "Optional chaining (?.) no es seguro en el POS de v11; usa &&.")
                    if re.search(r"!=\s*null\b", line):
                        add(WARN, path, line_no, "nullCheck", "!= null acepta false/0/''; si buscas un valor usa if (x).")
                    if re.search(r"\.off\s*\(\s*[\"'][^\"']+[\"']\s*\)", line):
                        add(WARN, path, line_no, "offSinHandler", "off(evento) sin handler borra todos los suscriptores del socket.")
                    if re.search(r"console\.log", line):
                        add(WARN, path, line_no, "consoleLog", "console.log en JS.")

        # .po masivos
        for status, path in mod_files:
            if path.endswith(".po"):
                out = git(repo, "diff", "--numstat", "%s...%s" % (args.base, args.head), "--", path)
                for line in out.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        if int(parts[0]) + int(parts[1]) > 60:
                            add(WARN, path, 0, "poMasivo",
                                "El .po cambia %s lineas: limita el diff a las cadenas de esta tarea." % (int(parts[0]) + int(parts[1])))

        # README / changelog
        readme = any(p.endswith(("README.rst", "README.md")) for _, p in mod_files if module_of(p) == mod)
        history = any("readme/HISTORY.rst" in p or p.endswith("CHANGELOG.md") for _, p in mod_files)
        is_new = old_manifest is None
        if is_new and not readme:
            add(WARN, "addons/%s/README.rst" % mod, 0, "readmeAusente",
                "Modulo nuevo sin README: el revisor lo pide.")
        if not is_new and code_files and not readme and not history:
            add(INFO, "addons/%s/README.rst" % mod, 0, "readmeSinCambios",
                "Cambios funcionales sin tocar README/HISTORY: valora si el cambio debe documentarse.")

    return emit(findings, args.json)


def emit(findings, as_json):
    findings.sort(key=lambda f: (SEV_ORDER.get(f.sev, 9), f.path, f.line))
    if as_json:
        print(json.dumps([f.as_dict() for f in findings], indent=2, ensure_ascii=False))
    else:
        if not findings:
            print("OK: no se han detectado patrones de riesgo.")
        for f in findings:
            loc = f.path + ((":" + str(f.line)) if f.line else "")
            print("[%s] %s  (%s)\n    %s" % (f.sev, loc, f.rule, f.msg))
        errors = sum(1 for f in findings if f.sev == ERROR)
        warns = sum(1 for f in findings if f.sev == WARN)
        print("\nResumen: %d ERROR, %d WARN, %d INFO" % (errors, warns, len(findings) - errors - warns))
    return 1 if any(f.sev == ERROR for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())

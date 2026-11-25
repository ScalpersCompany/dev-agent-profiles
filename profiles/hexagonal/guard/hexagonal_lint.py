#!/usr/bin/env python3
"""Guard the hexagonal dependency rule and the no-print rule."""

import argparse
import ast
import sys
from pathlib import Path

FORBIDDEN_ROOTS = {
    "fastapi",
    "starlette",
    "pydantic",
    "sqlalchemy",
    "sqlite3",
    "psycopg2",
    "requests",
    "httpx",
    "yaml",
    "redis",
    "celery",
    "boto3",
    "botocore",
    "kafka",
    "pika",
    "uvicorn",
}
FORBIDDEN_PARTS = {"infrastructure", "api"}
DOMAIN_PATTERNS = ("services/*/src/*/domain", "src/*/domain", "*/src/*/domain")


def domain_dirs(root):
    found = set()
    for pattern in DOMAIN_PATTERNS:
        found.update(path for path in root.glob(pattern) if path.is_dir())
    return sorted(found)


def source_files(root, staged):
    if staged:
        candidates = [root / name for name in staged]
        return [path for path in candidates if path.is_file() and path.suffix == ".py"]
    files = []
    for pattern in ("services/*/src", "src", "*/src"):
        for base in root.glob(pattern):
            if base.is_dir():
                files.extend(base.rglob("*.py"))
    return sorted(set(files))


def imported_modules(node):
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name
    elif isinstance(node, ast.ImportFrom):
        if node.level:
            if node.module:
                yield node.module
            return
        if node.module:
            yield node.module


def forbidden_import(module, domain_dir):
    parts = module.split(".")
    if parts[0] in FORBIDDEN_ROOTS:
        return module
    if any(part in FORBIDDEN_PARTS for part in parts):
        return module
    if parts[0] == domain_dir.name and len(parts) > 1 and parts[1] in FORBIDDEN_PARTS:
        return module
    return None


def check_imports(path, domain_dir):
    findings = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return ["%s:%s: syntax error: %s" % (path, exc.lineno, exc.msg)]
    for node in ast.walk(tree):
        for module in imported_modules(node):
            bad = forbidden_import(module, domain_dir)
            if bad:
                findings.append("%s:%s: forbidden import '%s'" % (path, node.lineno, bad))
    return findings


def check_prints(path):
    findings = []
    if "tests" in path.parts:
        return findings
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            findings.append("%s:%s: print() is not allowed" % (path, node.lineno))
    return findings


def main():
    parser = argparse.ArgumentParser(description="Check the hexagonal architecture guard")
    parser.add_argument("--root", default=".")
    parser.add_argument("--files", nargs="*", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    staged = [Path(name) for name in args.files] if args.files is not None else None
    findings = []
    domains = domain_dirs(root)
    files = source_files(root, staged)
    for path in files:
        for domain_dir in domains:
            try:
                path.relative_to(domain_dir)
            except ValueError:
                continue
            findings.extend(check_imports(path, domain_dir))
            break
        findings.extend(check_prints(path))
    for finding in sorted(set(findings)):
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

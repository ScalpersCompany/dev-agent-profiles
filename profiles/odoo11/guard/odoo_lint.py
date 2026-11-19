#!/usr/bin/env python3
"""Deterministic Odoo checks: sudo, cursor commits, raw SQL writes, stray prints.

Exit 1 on findings, 0 when clean. Warnings fail too unless --warn-only is set.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import sys
from pathlib import Path
from typing import Optional

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".mypy_cache", "evals"}
WRITE_SQL = ("INSERT ", "UPDATE ", "DELETE ", "ALTER ", "DROP ", "TRUNCATE ")


def load_allowlist(root: Path, path_arg: Optional[str] = None) -> list[str]:
    path = Path(path_arg) if path_arg else root / "guard" / "odoo_allowlist.txt"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def allowed(rel: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, pattern) for pattern in patterns)


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def has_py_interpolation(sql: str) -> bool:
    """True only for real string interpolation, not for DB-API placeholders."""
    import re

    without_placeholders = re.sub(r"%\([^)]+\)s|%s|%%", "", sql)
    return "%" in without_placeholders


def literal_sql(node: ast.AST) -> tuple[str, bool]:
    """Return the SQL text and whether it is interpolated."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, has_py_interpolation(node.value)
    if (
        isinstance(node, ast.BinOp)
        and isinstance(node.left, ast.Constant)
        and isinstance(node.left.value, str)
    ):
        return node.left.value, True
    if isinstance(node, ast.JoinedStr):
        text = "".join(
            value.value
            for value in node.values
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        )
        return text, True
    return "", False


def scan_file(path: Path, root: Path, patterns: list[str], warn_only: bool) -> list[tuple[str, int, str, str]]:
    rel = str(path.relative_to(root))
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []

    findings: list[tuple[str, int, str, str]] = []
    is_test = "/tests/" in f"/{rel}" or rel.endswith("_test.py")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = call_name(node.func)
            if name == "sudo" and not allowed(rel, patterns):
                findings.append((rel, node.lineno, "BLOCKER", "sudo() outside guard/odoo_allowlist.txt"))
            if name == "commit" and isinstance(node.func, ast.Attribute) and call_name(node.func.value) == "cr":
                findings.append((rel, node.lineno, "BLOCKER", "cr.commit() in business code"))
            if name == "execute" and node.args:
                sql, interpolated = literal_sql(node.args[0])
                if sql:
                    upper = sql.upper()
                    if any(token in upper for token in WRITE_SQL):
                        detail = "raw SQL write; use the ORM or parameterized SQL with a test"
                        if interpolated:
                            detail += "; interpolation detected"
                        findings.append((rel, node.lineno, "BLOCKER", detail))
                    elif "SELECT" in upper and interpolated:
                        findings.append((rel, node.lineno, "WARNING", "SQL string interpolation; use parameters"))
            if name == "print" and not is_test:
                findings.append((rel, node.lineno, "WARNING", "print() outside tests; use the logger"))

    return findings


def module_roots(root: Path) -> list[Path]:
    roots = []
    for manifest in root.rglob("__manifest__.py"):
        rel_parts = manifest.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        roots.append(manifest.parent)
    return roots


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--files", nargs="*", default=None)
    parser.add_argument("--allowlist")
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    patterns = load_allowlist(root, args.allowlist)
    findings: list[tuple[str, int, str, str]] = []

    if args.files is not None:
        for name in args.files:
            path = (root / name).resolve()
            if not path.is_file() or path.suffix != ".py":
                continue
            try:
                rel_parts = path.relative_to(root).parts
            except ValueError:
                continue
            if any(part in SKIP_DIRS for part in rel_parts):
                continue
            findings.extend(scan_file(path, root, patterns, args.warn_only))
        if not args.files:
            print("odoo_lint: no files to scan")
    else:
        roots = module_roots(root)
        if not roots:
            print("odoo_lint: no Odoo modules found, nothing to scan")
            return 0

        for module_root in roots:
            for path in module_root.rglob("*.py"):
                rel_parts = path.relative_to(root).parts
                if any(part in SKIP_DIRS for part in rel_parts):
                    continue
                findings.extend(scan_file(path, root, patterns, args.warn_only))

    for rel, line, severity, message in sorted(findings):
        print(f"{rel}:{line}: {severity} {message}")

    blockers = [f for f in findings if f[2] == "BLOCKER"]
    if blockers:
        return 1
    if findings and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

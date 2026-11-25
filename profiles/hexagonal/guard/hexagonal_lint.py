#!/usr/bin/env python3
"""Guard the hexagonal dependency rule and the no-print rule."""

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path

FORBIDDEN_SUBMODULES = {"application", "infrastructure", "api"}
IGNORED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "site-packages",
    "tests",
    "docs",
}
STDLIB = set(getattr(sys, "stdlib_module_names", set(sys.builtin_module_names)))
SOURCE_PATTERNS = ("services/*/src", "services/*/app", "src", "app", "*/src", "*/app")


def walk_python(base):
    for current, dirs, files in os.walk(base):
        dirs[:] = [name for name in dirs if name not in IGNORED_PARTS]
        for name in files:
            if name.endswith(".py"):
                yield Path(current) / name


def domain_dirs(root):
    found = []
    for current, dirs, _files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_PARTS]
        path = Path(current)
        if path.name == "domain":
            found.append(path)
    return sorted(found)


def domain_files(domains):
    files = set()
    for directory in domains:
        files.update(walk_python(directory))
    return sorted(files)


def source_roots(root):
    roots = set()
    for pattern in SOURCE_PATTERNS:
        roots.update(path for path in root.glob(pattern) if path.is_dir())
    return sorted(roots)


def source_files(root, staged):
    if staged is not None:
        return [root / name for name in staged if (root / name).suffix == ".py"]
    files = set()
    for base in source_roots(root):
        files.update(walk_python(base))
    return sorted(files)


def read_source(path, root, staged):
    if staged:
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            return None
        try:
            output = subprocess.check_output(
                ["git", "-C", str(root), "show", ":./" + rel],
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        try:
            return output.decode("utf-8")
        except UnicodeDecodeError:
            return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def package_for(domain_dir, root):
    parent = domain_dir.parent
    if parent == root or parent.name in {"src", "app"}:
        return domain_dir.name
    return parent.name


def import_problem(module, names, level, package, domain_package):
    if level:
        if module:
            parts = module.split(".")
            if any(part in FORBIDDEN_SUBMODULES for part in parts):
                return module
        for name in names:
            if name in FORBIDDEN_SUBMODULES:
                return name
        return None
    if not module:
        return None
    parts = module.split(".")
    if parts[0] in STDLIB:
        return None
    if parts[0] in {"src", "app"}:
        if any(part in FORBIDDEN_SUBMODULES for part in parts[1:]):
            return module
        if any(name in FORBIDDEN_SUBMODULES for name in names):
            return module
        if "domain" in parts[1:] or "domain" in names:
            return None
    if package and parts[0] == package:
        if any(part in FORBIDDEN_SUBMODULES for part in parts[1:]):
            return module
        if any(name in FORBIDDEN_SUBMODULES for name in names):
            return module
        if domain_package:
            return None
        if "domain" in parts[1:] or ("domain" in names and len(parts) == 1):
            return None
        return module
    return module


def _dynamic_problem(node, package, domain_package, importlib_aliases, import_aliases, builtins_aliases):
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    is_import = isinstance(func, ast.Name) and (
        func.id == "__import__" or func.id in import_aliases
    )
    if isinstance(func, ast.Name) and func.id in importlib_aliases:
        is_import = True
    if (
        isinstance(func, ast.Attribute)
        and func.attr == "import_module"
        and isinstance(func.value, ast.Name)
        and func.value.id in importlib_aliases | {"importlib"}
    ):
        is_import = True
    if (
        isinstance(func, ast.Attribute)
        and func.attr == "__import__"
        and isinstance(func.value, ast.Name)
        and func.value.id in builtins_aliases | {"builtins"}
    ):
        is_import = True
    if not is_import or not node.args:
        return None
    argument = node.args[0]
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        return import_problem(argument.value, [], 0, package, domain_package)
    return None


def check_imports(source, path, package, domain_package):
    findings = []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return ["%s:%s: syntax error: %s" % (path, exc.lineno, exc.msg)]
    importlib_aliases = set()
    import_aliases = set()
    builtins_aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "importlib":
            for alias in node.names:
                if alias.name == "import_module":
                    importlib_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "builtins":
            for alias in node.names:
                if alias.name == "__import__":
                    import_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    importlib_aliases.add(alias.asname or alias.name)
                elif alias.name == "builtins":
                    builtins_aliases.add(alias.asname or alias.name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                problem = import_problem(alias.name, [], 0, package, domain_package)
                if problem:
                    findings.append("%s:%s: forbidden import '%s'" % (path, node.lineno, problem))
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            problem = import_problem(node.module or "", names, node.level, package, domain_package)
            if problem:
                findings.append("%s:%s: forbidden import '%s'" % (path, node.lineno, problem))
        else:
            problem = _dynamic_problem(
                node,
                package,
                domain_package,
                importlib_aliases,
                import_aliases,
                builtins_aliases,
            )
            if problem:
                findings.append("%s:%s: forbidden import '%s'" % (path, node.lineno, problem))
    return findings


def check_prints(source, path, root):
    findings = []
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    if "tests" in relative.parts:
        return findings
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return ["%s:%s: syntax error: %s" % (path, exc.lineno, exc.msg)]
    print_aliases = set()
    builtins_aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "builtins":
            for alias in node.names:
                if alias.name == "print":
                    print_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "builtins":
                    builtins_aliases.add(alias.asname or alias.name)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and (func.id == "print" or func.id in print_aliases):
            findings.append("%s:%s: print() is not allowed" % (path, node.lineno))
        elif (
            isinstance(func, ast.Attribute)
            and func.attr == "print"
            and isinstance(func.value, ast.Name)
            and func.value.id in builtins_aliases | {"builtins"}
        ):
            findings.append("%s:%s: print() is not allowed" % (path, node.lineno))
    return findings


def _is_inside(path, directory):
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser(description="Check the hexagonal architecture guard")
    parser.add_argument("--root", default=".")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--files", nargs="*", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    domains = domain_dirs(root)
    if not domains:
        print("hexagonal: no domain directory found under %s" % root, file=sys.stderr)
        return 1
    domain_paths = domain_files(domains)
    if not args.staged and not domain_paths:
        print("hexagonal: no Python files under domain directories", file=sys.stderr)
        return 1
    staged_files = args.files if args.staged else None
    if args.staged:
        roots = source_roots(root)
        files = set()
        for path in source_files(root, staged_files):
            try:
                relative = path.relative_to(root)
            except ValueError:
                continue
            if any(part in IGNORED_PARTS for part in relative.parts):
                continue
            if any(_is_inside(path, directory) for directory in domains) or any(
                _is_inside(path, base) for base in roots
            ):
                files.add(path)
    else:
        files = set(domain_paths) | set(source_files(root, None))
    findings = []
    for path in sorted(files):
        source = read_source(path, root, args.staged)
        if source is None:
            findings.append("%s: cannot read source" % path)
            continue
        for directory in domains:
            if _is_inside(path, directory):
                package = package_for(directory, root)
                findings.extend(
                    check_imports(source, path, package, package == directory.name)
                )
                break
        findings.extend(check_prints(source, path, root))
    for finding in sorted(set(findings)):
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LINT = Path(__file__).resolve().parents[1] / "guard" / "hexagonal_lint.py"
GUARD = Path(__file__).resolve().parents[1] / "guard" / "hexagonal.sh"


def run_lint(root, *args):
    return subprocess.run(
        [sys.executable, str(LINT), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestHexagonalLint(unittest.TestCase):
    def test_clean_domain_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "services" / "demo" / "src" / "demo" / "domain" / "entities.py",
                "from dataclasses import dataclass\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_third_party_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "domain" / "entities.py", "import numpy\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("forbidden import", result.stdout)

    def test_application_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from demo.application import use_case\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("application", result.stdout)

    def test_own_domain_import_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from demo.domain.value_objects import Money\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_relative_application_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from .. import application\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("application", result.stdout)

    def test_relative_infrastructure_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from ...infrastructure import repo\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("infrastructure", result.stdout)

    def test_print_in_service_code_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "services" / "demo" / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            write(root / "services" / "demo" / "src" / "demo" / "api" / "main.py", "print('debug')\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("print()", result.stdout)

    def test_builtins_print_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "services" / "demo" / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            write(
                root / "services" / "demo" / "src" / "demo" / "api" / "main.py",
                "import builtins\nbuiltins.print('debug')\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("print()", result.stdout)

    def test_relative_infrastructure_without_module_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from .. import infrastructure\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("infrastructure", result.stdout)

    def test_own_domain_from_package_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from demo import domain\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_print_in_tests_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            write(root / "src" / "demo" / "tests" / "test_x.py", "print('debug')\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_missing_domain_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "api" / "main.py", "x = 1\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no domain directory", result.stderr)

    def test_non_utf8_file_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "src" / "demo" / "domain" / "entities.py"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"\xff\xfe")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read source", result.stdout)

    def test_staged_reads_the_index_not_the_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            path = root / "services" / "demo" / "src" / "demo" / "domain" / "entities.py"
            write(path, "from fastapi import FastAPI\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            write(path, "from dataclasses import dataclass\n")
            result = run_lint(
                root,
                "--staged",
                "--files",
                "services/demo/src/demo/domain/entities.py",
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("fastapi", result.stdout)

    def test_domain_outside_source_patterns_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "services" / "x" / "pkg" / "domain" / "entities.py",
                "from fastapi import FastAPI\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("fastapi", result.stdout)

    def test_root_path_with_tests_component_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tests" / "project"
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_third_party_with_domain_segment_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for text in (
                "from sqlalchemy.domain import x\n",
                "from fastapi import domain\n",
                "import requests.domain\n",
            ):
                write(root / "src" / "demo" / "domain" / "entities.py", text)
                result = run_lint(root)
                self.assertEqual(result.returncode, 1, text)
        self.assertTrue(True)

    def test_builtins_print_alias_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            write(
                root / "src" / "demo" / "api" / "main.py",
                "from builtins import print as pr\npr('debug')\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("print()", result.stdout)

    def test_guard_happy_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            result = subprocess.run(
                ["bash", str(GUARD)],
                cwd=root,
                capture_output=True,
                text=True,
                env={"GUARD_ROOT": str(root), "PATH": "/usr/bin:/bin"},
            )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_guard_staged_from_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root / "sub"
            sub.mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            write(sub / "src" / "demo" / "domain" / "entities.py", "from fastapi import FastAPI\n")
            subprocess.run(["git", "add", "sub"], cwd=root, check=True)
            result = subprocess.run(
                ["bash", str(GUARD), "--staged"],
                cwd=sub,
                capture_output=True,
                text=True,
                env={"GUARD_ROOT": str(sub), "PATH": "/usr/bin:/bin"},
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("fastapi", result.stdout)

    def test_staged_syntax_error_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            path = root / "src" / "demo" / "domain" / "entities.py"
            path.parent.mkdir(parents=True)
            path.write_text("def broken(\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            result = run_lint(root, "--staged", "--files", "src/demo/domain/entities.py")
        self.assertEqual(result.returncode, 1)
        self.assertIn("syntax error", result.stdout)

    def test_ignored_directories_are_pruned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            write(root / "src" / "node_modules" / "x" / "m.py", "print('noise')\n")
            write(root / "src" / ".venv" / "lib" / "m.py", "print('noise')\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_staged_does_not_read_untracked_domain_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            write(root / "src" / "demo" / "domain" / "untracked.py", "y = 1\n")
            result = run_lint(root, "--staged", "--files", "src/demo/domain/entities.py")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_domain_package_layout_accepts_own_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "domain" / "value.py", "from domain.value import X\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_builtins_module_alias_print_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            write(
                root / "src" / "demo" / "api" / "main.py",
                "import builtins as b\nb.print('debug')\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("print()", result.stdout)

    def test_relative_shared_infrastructure_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from ..shared.infrastructure import x\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("infrastructure", result.stdout)

    def test_dynamic_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "import importlib\nimportlib.import_module('fastapi')\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("fastapi", result.stdout)

    def test_staged_ignores_ignored_and_outside_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            write(root / "src" / ".venv" / "x" / "domain" / "p.py", "print('noise')\n")
            write(root / "scripts" / "s.py", "print('noise')\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            result = run_lint(
                root,
                "--staged",
                "--files",
                "src/demo/domain/entities.py",
                "src/.venv/x/domain/p.py",
                "scripts/s.py",
            )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_src_domain_absolute_prefix_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "domain" / "value.py", "from src.domain import x\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_importlib_alias_dynamic_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from importlib import import_module\nimport_module('fastapi')\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("fastapi", result.stdout)

    def test_src_package_domain_import_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "domain" / "value.py", "from src import domain\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_builtins_dunder_import_alias_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from builtins import __import__ as q\nq('requests')\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("requests", result.stdout)

    def test_builtins_module_dunder_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "import builtins as b\nb.__import__('yaml')\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("yaml", result.stdout)

    def test_syntax_error_outside_domain_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            write(root / "src" / "demo" / "api" / "main.py", "def broken(\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("syntax error", result.stdout)

    def test_stdlib_io_modules_are_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for text in ("import sqlite3\n", "import urllib.request\n", "import subprocess\n"):
                write(root / "src" / "demo" / "domain" / "entities.py", text)
                result = run_lint(root)
                self.assertEqual(result.returncode, 1, text)
        self.assertTrue(True)

    def test_relative_sibling_config_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from ..config import S\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("config", result.stdout)

    def test_relative_sibling_domain_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from ..domain import X\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_relative_current_domain_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from .entities import X\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_src_domain_relative_sibling_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "domain" / "value.py", "from ..config import S\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("config", result.stdout)

    def test_own_package_config_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for text in (
                "from svc.config import Settings\n",
                "import svc.config\n",
                "from svc import config\n",
            ):
                write(root / "src" / "svc" / "domain" / "entities.py", text)
                result = run_lint(root)
                self.assertEqual(result.returncode, 1, text)
        self.assertTrue(True)

    def test_own_package_domain_import_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "svc" / "domain" / "entities.py", "from svc import domain\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_pathlib_in_domain_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "svc" / "domain" / "entities.py", "import pathlib\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("pathlib", result.stdout)

    def test_more_stdlib_io_modules_are_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for text in (
                "import glob\n",
                "import zipfile\n",
                "import gzip\n",
                "import tarfile\n",
                "import logging.handlers\n",
                "from logging import config\n",
            ):
                write(root / "src" / "demo" / "domain" / "entities.py", text)
                result = run_lint(root)
                self.assertEqual(result.returncode, 1, text)
        self.assertTrue(True)

    def test_open_in_domain_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "data = open('x').read()\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("open()", result.stdout)

    def test_files_without_staged_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "domain" / "entities.py", "x = 1\n")
            result = run_lint(root, "--files", "src/demo/domain/entities.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--files requires --staged", result.stderr)

    def test_builtins_open_alias_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "from builtins import open as o\no('x')\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("open()", result.stdout)

    def test_builtins_module_open_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "src" / "demo" / "domain" / "entities.py",
                "import builtins as b\nb.open('x')\n",
            )
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("open()", result.stdout)

    def test_guard_staged_failure_outside_a_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "src" / "demo" / "domain" / "entities.py", "import fastapi\n")
            result = subprocess.run(
                ["bash", str(GUARD), "--staged"],
                cwd=root,
                capture_output=True,
                text=True,
                env={
                    "GUARD_ROOT": str(root),
                    "GIT_CEILING_DIRECTORIES": str(root.parent),
                    "PATH": "/usr/bin:/bin",
                },
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("git diff failed", result.stderr)


if __name__ == "__main__":
    unittest.main()

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LINT = Path(__file__).resolve().parents[1] / "guard" / "hexagonal_lint.py"


def run_lint(root):
    return subprocess.run(
        [sys.executable, str(LINT), "--root", str(root)],
        capture_output=True,
        text=True,
    )


class TestHexagonalLint(unittest.TestCase):
    def test_clean_domain_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            domain = root / "services" / "demo" / "src" / "demo" / "domain"
            domain.mkdir(parents=True)
            (domain / "entities.py").write_text("from dataclasses import dataclass\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_framework_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            domain = root / "services" / "demo" / "src" / "demo" / "domain"
            domain.mkdir(parents=True)
            (domain / "entities.py").write_text("from fastapi import FastAPI\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("forbidden import", result.stdout)

    def test_relative_infrastructure_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            domain = root / "src" / "demo" / "domain"
            domain.mkdir(parents=True)
            (domain / "entities.py").write_text("from ...infrastructure import repo\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("infrastructure", result.stdout)

    def test_print_in_service_code_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            api = root / "services" / "demo" / "src" / "demo" / "api"
            api.mkdir(parents=True)
            (api / "main.py").write_text("print('debug')\n")
            result = run_lint(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("print()", result.stdout)


if __name__ == "__main__":
    unittest.main()

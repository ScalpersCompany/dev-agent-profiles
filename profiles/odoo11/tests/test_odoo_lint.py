import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
LINT = KIT / "guard" / "odoo_lint.py"
ALLOWLIST = KIT / "guard" / "odoo_allowlist.txt"


def write_module(root: Path, name: str, body: str) -> Path:
    module = root / "addons" / name
    (module / "models").mkdir(parents=True)
    (module / "__manifest__.py").write_text(
        "{'name': '%s', 'version': '11.0.1.0.0'}\n" % name, encoding="utf-8"
    )
    path = module / "models" / "model.py"
    path.write_text(body, encoding="utf-8")
    return path


def run_lint(root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(LINT),
            "--root",
            str(root),
            "--allowlist",
            str(ALLOWLIST),
            *extra,
        ],
        capture_output=True,
        text=True,
    )


class OdooLintTest(unittest.TestCase):
    def test_parameterized_sql_is_not_interpolation(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            write_module(
                root,
                "safe",
                "def f(self):\n"
                "    self.env.cr.execute('SELECT id FROM res_partner WHERE id = %s', (1,))\n",
            )
            result = run_lint(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_full_scan_blocks_business_code(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            write_module(
                root,
                "bad",
                "def f(self):\n"
                "    self.env.cr.commit()\n"
                "    self.env['res.partner'].sudo().search([])\n"
                "    print('x')\n"
                "    self.env.cr.execute('DELETE FROM res_partner WHERE id = %s' % 1)\n",
            )
            result = run_lint(root)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("BLOCKER", result.stdout)
            self.assertIn("cr.commit", result.stdout)
            self.assertIn("interpolation detected", result.stdout)

    def test_files_mode_ignores_an_unrelated_bad_module(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            write_module(root, "bad", "def f(self):\n    self.env.cr.commit()\n")
            good = write_module(root, "good", "def f(self):\n    return self.env['res.partner'].search([])\n")
            result = run_lint(root, "--files", str(good.relative_to(root)))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_files_mode_blocks_the_staged_bad_file(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            bad = write_module(root, "bad", "def f(self):\n    print('x')\n")
            result = run_lint(root, "--files", str(bad.relative_to(root)))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("print() outside tests", result.stdout)


if __name__ == "__main__":
    unittest.main()

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FLOW = Path(__file__).resolve().parents[1]
LINT = FLOW / "guard" / "team_lint.py"


def run_lint(*args):
    return subprocess.run(
        [sys.executable, str(LINT), *args],
        capture_output=True,
        text=True,
    )


class TestTeamLint(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="team-lint-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.copy = self.tmp / "team"
        shutil.copytree(FLOW, self.copy)

    def roles(self):
        return json.loads((self.copy / "roles.json").read_text(encoding="utf-8"))

    def save_roles(self, data):
        (self.copy / "roles.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    def role(self, data, name):
        return next(item for item in data["roles"] if item["role"] == name)

    def write_task(self, body):
        path = self.tmp / "feature.md"
        path.write_text(body, encoding="utf-8")
        return path

    def test_real_profile_passes(self):
        result = run_lint("--profile", str(FLOW))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok:", result.stdout)

    def test_readonly_role_with_writes_is_rejected(self):
        data = self.roles()
        self.role(data, "review")["writes"] = ["addons/anything/**"]
        self.save_roles(data)
        result = run_lint("--profile", str(self.copy))
        self.assertEqual(result.returncode, 1)
        self.assertIn("read-only and declares writes", result.stderr)

    def test_readonly_role_outside_the_copy_is_rejected(self):
        data = self.roles()
        self.role(data, "verify")["runs_on_copy"] = False
        self.save_roles(data)
        result = run_lint("--profile", str(self.copy))
        self.assertEqual(result.returncode, 1)
        self.assertIn("must run on a copy", result.stderr)

    def test_exit_command_outside_the_kit_is_rejected(self):
        data = self.roles()
        self.role(data, "judge")["exit"] = [{"command": "bash deploy.sh", "expect": "exit 0"}]
        self.save_roles(data)
        result = run_lint("--profile", str(self.copy))
        self.assertEqual(result.returncode, 1)
        self.assertIn("outside the kit command list", result.stderr)

    def test_undeclared_placeholder_is_rejected(self):
        data = self.roles()
        self.role(data, "dev")["writes"] = ["addons/{component}/**"]
        self.save_roles(data)
        result = run_lint("--profile", str(self.copy))
        self.assertEqual(result.returncode, 1)
        self.assertIn("undeclared placeholder", result.stderr)

    def test_second_worktree_owner_is_rejected(self):
        data = self.roles()
        self.role(data, "plan")["owns_worktree"] = True
        self.save_roles(data)
        result = run_lint("--profile", str(self.copy))
        self.assertEqual(result.returncode, 1)
        self.assertIn("only role that owns the worktree", result.stderr)

    def test_task_file_with_linked_specs_passes(self):
        path = self.write_task(
            "# Feature\n\n## Specs\n\n- S1: the rule\n- S2: the other rule\n\n"
            "## Tasks\n\n- T1 (S1): one\n- T2 (S1, S2): two\n\n"
            "## Log\n\n- L1: \"do it\" (2026-11-26)\n"
        )
        result = run_lint("--task", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_task_without_spec_reference_is_rejected(self):
        path = self.write_task(
            "# Feature\n\n## Specs\n\n- S1: the rule\n\n"
            "## Tasks\n\n- T1: one\n\n## Log\n\n- L1: \"do it\"\n"
        )
        result = run_lint("--task", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("without an S# reference", result.stderr)

    def test_task_citing_unknown_spec_is_rejected(self):
        path = self.write_task(
            "# Feature\n\n## Specs\n\n- S1: the rule\n\n"
            "## Tasks\n\n- T1 (S3): one\n\n## Log\n\n- L1: \"do it\"\n"
        )
        result = run_lint("--task", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown spec", result.stderr)

    def test_task_table_with_em_dash_scaffolding_passes(self):
        path = self.write_task(
            "# Feature\n\n## Specs\n\n- S1: the rule\n\n"
            "## Tasks\n\n| ID | Spec | Ruta | Estado |\n|---|---|---|---|\n"
            "| T0 | — | module skeleton | done |\n"
            "| T1 | S1 | the change | done |\n\n"
            "## Evidencia\n\n- T9: this is not a task row and must be ignored\n\n"
            "## Log\n\n- L1: \"do it\"\n"
        )
        result = run_lint("--task", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_task_without_l1_is_rejected(self):
        path = self.write_task(
            "# Feature\n\n## Specs\n\n- S1: the rule\n\n"
            "## Tasks\n\n- T1 (S1): one\n\n## Log\n\n- a note\n"
        )
        result = run_lint("--task", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("log must start with L1", result.stderr)

    def test_evidence_with_a_passing_summary_passes(self):
        run_dir = self.tmp / "evidence" / "20260101T000000-abc123"
        run_dir.mkdir(parents=True)
        (run_dir / "summary.json").write_text(
            json.dumps(
                {
                    "run_id": "20260101T000000-abc123",
                    "sha": "abc123",
                    "boot": "started",
                    "health": "pass",
                    "smoke": "pass",
                    "tests": "pass",
                    "e2e": "skipped",
                    "status": "pass",
                }
            ),
            encoding="utf-8",
        )
        result = run_lint("--evidence", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_evidence_with_a_skipped_suite_is_rejected(self):
        run_dir = self.tmp / "evidence" / "run"
        run_dir.mkdir(parents=True)
        (run_dir / "summary.json").write_text(
            json.dumps(
                {
                    "run_id": "run",
                    "sha": "abc123",
                    "tests": "skipped",
                    "e2e": "skipped",
                    "status": "pass",
                }
            ),
            encoding="utf-8",
        )
        result = run_lint("--evidence", str(run_dir))
        self.assertEqual(result.returncode, 1)
        self.assertIn("tests is skipped", result.stderr)
        self.assertIn("no check ran", result.stderr)

    def test_score_requires_k_and_a_different_judge(self):
        score = self.tmp / "score.json"
        payload = {
            "k": 3,
            "passed": True,
            "threshold": 8.5,
            "aggregate": {"mean": 9.1},
            "model": "executor-model",
            "judge_model": "judge-model",
        }
        score.write_text(json.dumps(payload), encoding="utf-8")
        self.assertEqual(run_lint("--score", str(score)).returncode, 0)
        payload["judge_model"] = "executor-model"
        score.write_text(json.dumps(payload), encoding="utf-8")
        result = run_lint("--score", str(score))
        self.assertEqual(result.returncode, 1)
        self.assertIn("judge_model equals model", result.stderr)

    def test_tree_snapshot_detects_a_change(self):
        tree = self.tmp / "tree"
        tree.mkdir()
        (tree / "file.txt").write_text("one\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tree), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(tree), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(tree),
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@example.com",
                "commit",
                "-qm",
                "init",
            ],
            check=True,
        )
        snapshot = run_lint("--tree-snapshot", str(tree))
        self.assertEqual(snapshot.returncode, 0, snapshot.stderr)
        digest = snapshot.stdout.strip()
        unchanged = run_lint("--tree-unchanged", str(tree), digest)
        self.assertEqual(unchanged.returncode, 0, unchanged.stderr)
        (tree / "file.txt").write_text("two\n", encoding="utf-8")
        changed = run_lint("--tree-unchanged", str(tree), digest)
        self.assertEqual(changed.returncode, 1)
        self.assertIn("tree changed", changed.stderr)

    def test_missing_entrypoint_is_rejected(self):
        data = json.loads((self.copy / "flow.json").read_text(encoding="utf-8"))
        data["entrypoint"] = "bin/nope.sh"
        (self.copy / "flow.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = run_lint("--profile", str(self.copy))
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing entrypoint: bin/nope.sh", result.stderr)

    def test_entrypoint_without_the_execute_bit_is_rejected(self):
        runner = self.copy / "bin" / "team-run.sh"
        runner.chmod(0o644)
        result = run_lint("--profile", str(self.copy))
        self.assertEqual(result.returncode, 1)
        self.assertIn("entrypoint is not executable", result.stderr)


if __name__ == "__main__":
    unittest.main()

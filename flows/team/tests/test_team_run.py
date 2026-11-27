import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

FLOW = Path(__file__).resolve().parents[1]
RUNNER = FLOW / "bin" / "team-run.sh"

TASK_FILE = (
    "# Demo\n\n"
    "## Specs\n\n"
    "- S1: the rule\n\n"
    "## Tasks\n\n"
    "- T1 (S1): one\n\n"
    "## Log\n\n"
    '- L1: "do it"\n'
)


class TeamRunCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="team-run-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        (self.repo / "odd" / "tasks").mkdir(parents=True)
        (self.repo / ".dev-agent" / "profiles").mkdir(parents=True)
        shutil.copytree(FLOW, self.repo / ".dev-agent" / "profiles" / "team")
        self.write_task(TASK_FILE)

    def write_task(self, body):
        (self.repo / "odd" / "tasks" / "demo.md").write_text(body, encoding="utf-8")

    def write_makefile(self, body="check:\n\t@echo check-ok\n"):
        (self.repo / "Makefile").write_text(body, encoding="utf-8")

    def write_verify_env(self, body):
        (self.repo / ".dev-agent" / "verify.env").write_text(body, encoding="utf-8")

    def stub_cli(self, body):
        path = self.tmp / "cli.sh"
        path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
        path.chmod(0o755)
        return path

    def run_team(self, *args, stub=True, run_id="run1", env=None):
        command = ["bash", str(RUNNER), str(self.repo)]
        command += ["--spec", "odd/tasks/demo.md"]
        if stub:
            command.append("--stub-cli")
        command += list(args)
        environment = dict(os.environ)
        environment["TEAM_RUN_ID"] = run_id
        environment.pop("TEAM_SPEC", None)
        environment.update(env or {})
        result = subprocess.run(
            command, capture_output=True, text=True, cwd=str(self.tmp), env=environment
        )
        return result

    def run_dir(self, run_id="run1"):
        return self.repo / "evidence" / run_id

    def stage_order(self, output):
        order = []
        for line in output.splitlines():
            if line.startswith("== "):
                order.append(line[3:].strip())
        return order


class TestTeamRunChain(TeamRunCase):
    def test_full_chain_passes_in_fixed_order(self):
        self.write_makefile()
        result = self.run_team()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.stage_order(result.stdout), ["plan", "dev", "review", "verify"])
        self.assertIn("chain green", result.stdout)
        self.assertTrue((self.run_dir() / "review.md").is_file())
        self.assertTrue((self.run_dir() / "summary.json").is_file())
        self.assertTrue((self.run_dir() / "plan.team_lint.log").is_file())

    def test_summary_row_per_stage(self):
        self.write_makefile()
        result = self.run_team()
        summary = result.stdout.split("team-run: summary", 1)[1]
        for stage in ("plan", "dev", "review", "verify"):
            self.assertRegex(summary, r"(?m)^  %s +pass" % stage)

    def test_stops_at_the_first_failing_stage(self):
        self.write_makefile()
        result = self.run_team(env={"STUB_FAIL_ROLE": "dev"})
        self.assertEqual(result.returncode, 21, result.stdout + result.stderr)
        self.assertEqual(self.stage_order(result.stdout), ["plan", "dev"])
        self.assertIn("stopped at dev (exit 21)", result.stdout)
        self.assertTrue((self.run_dir() / "plan.log").is_file())
        self.assertFalse((self.run_dir() / "review.log").exists())
        self.assertFalse((self.run_dir() / "review.md").exists())

    def test_review_gate_rejects_a_verdict_that_is_not_passed(self):
        self.write_makefile()
        result = self.run_team(env={"STUB_REVIEW_STATUS": "FAILED"})
        self.assertEqual(result.returncode, 22, result.stdout + result.stderr)
        self.assertEqual(self.stage_order(result.stdout), ["plan", "dev", "review"])
        self.assertIn("verdict is not PASSED", result.stdout)
        self.assertFalse((self.run_dir() / "summary.json").exists())

    def test_verify_gate_rejects_evidence_that_says_failed(self):
        self.write_makefile()
        result = self.run_team(env={"STUB_VERIFY_STATUS": "failed"})
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn("evidence rejected", result.stdout)

    def test_verify_gate_rejects_a_run_without_summary(self):
        self.write_makefile()
        stub = self.stub_cli(
            'if [ "$TEAM_ROLE" = "review" ]; then printf "STATUS: PASSED\\n" > "$TEAM_VERDICT"; fi\n'
            "exit 0\n"
        )
        result = self.run_team("--stub-cli", str(stub), stub=False)
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn("evidence rejected", result.stdout)

    def test_plan_gate_rejects_a_task_file_without_log(self):
        self.write_makefile()
        self.write_task("# Demo\n\n## Specs\n\n- S1: the rule\n\n## Tasks\n\n- T1 (S1): one\n")
        result = self.run_team()
        self.assertEqual(result.returncode, 20, result.stdout + result.stderr)
        self.assertEqual(self.stage_order(result.stdout), ["plan"])
        self.assertIn("team_lint --task rejected", result.stdout)
        self.assertFalse((self.run_dir() / "dev.log").exists())

    def test_plan_gate_rejects_a_missing_task_file(self):
        self.write_makefile()
        (self.repo / "odd" / "tasks" / "demo.md").unlink()
        result = self.run_team()
        self.assertEqual(result.returncode, 20, result.stdout + result.stderr)
        self.assertIn("missing task file", result.stdout)

    def test_dev_gate_fails_when_the_repository_runner_fails(self):
        self.write_makefile("check:\n\t@echo boom >&2\n\t@exit 3\n")
        result = self.run_team()
        self.assertEqual(result.returncode, 21, result.stdout + result.stderr)
        self.assertIn("runner failed: make check", result.stdout)
        self.assertIn("boom", result.stdout)

    def test_dev_gate_uses_the_verify_env_runner_without_a_makefile(self):
        self.write_verify_env('VERIFY_CMD="printf verify-env-ran"\n')
        result = self.run_team()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = (self.run_dir() / "dev.runner.log").read_text(encoding="utf-8")
        self.assertIn("verify-env-ran", log)

    def test_dev_gate_fails_without_any_declared_runner(self):
        result = self.run_team()
        self.assertEqual(result.returncode, 21, result.stdout + result.stderr)
        self.assertIn("no repository runner", result.stdout)

    def test_from_stage_skips_the_earlier_ones(self):
        self.write_makefile()
        result = self.run_team("--from", "review")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.stage_order(result.stdout), ["review", "verify"])
        self.assertIn("skipped", result.stdout)
        self.assertFalse((self.run_dir() / "plan.log").exists())

    def test_stage_timeout_is_reported(self):
        self.write_makefile()
        stub = self.stub_cli("sleep 5\n")
        result = self.run_team(
            "--stub-cli", str(stub), stub=False, env={"TEAM_STAGE_TIMEOUT": "1"}
        )
        self.assertEqual(result.returncode, 20, result.stdout + result.stderr)
        self.assertIn("timed out after 1s", result.stdout)

    def test_cli_receives_the_profile_the_query_and_the_repo(self):
        self.write_makefile()
        record = self.tmp / "argv.txt"
        stub = self.stub_cli(
            'printf "%s\\t%s\\n" "$TEAM_ROLE" "$*" >> '
            + str(record)
            + '\nif [ "$TEAM_ROLE" = "review" ]; then printf "STATUS: PASSED\\n" > "$TEAM_VERDICT"; fi\nexit 0\n'
        )
        self.run_team("--stub-cli", str(stub), stub=False)
        lines = record.read_text(encoding="utf-8").splitlines()
        roles = [line.split("\t", 1)[0] for line in lines]
        self.assertEqual(roles, ["plan", "dev", "review", "verify"])
        command = lines[0].split("\t", 1)[1]
        self.assertTrue(command.startswith("-p plan chat -q Plan spec odd/tasks/demo.md"), command)
        self.assertIn(" -Q ", command)
        self.assertIn(" --in %s " % self.repo, command)
        self.assertTrue(command.endswith("--max-turns 40"), command)


class TestTeamRunDryRun(TeamRunCase):
    def test_dry_run_executes_nothing(self):
        self.write_makefile()
        marker = self.tmp / "called"
        stub = self.stub_cli("touch %s\nexit 0\n" % marker)
        result = self.run_team("--dry-run", "--stub-cli", str(stub), stub=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(marker.exists())
        self.assertFalse((self.repo / "evidence").exists())
        self.assertIn("no stage executed and nothing written", result.stdout)

    def test_dry_run_lists_every_stage_with_its_gate(self):
        self.write_makefile()
        result = self.run_team("--dry-run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.stage_order(result.stdout), [])
        for stage in ("plan", "dev", "review", "verify"):
            self.assertRegex(result.stdout, r"(?m)^%s +run +" % stage)
        self.assertIn("gate: task file odd/tasks/demo.md", result.stdout)


class TestTeamRunUsage(TeamRunCase):
    def test_repository_and_spec_are_required(self):
        result = subprocess.run(
            ["bash", str(RUNNER)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 10)
        self.assertIn("a repository and --spec are required", result.stderr)

    def test_unknown_from_stage_is_rejected(self):
        self.write_makefile()
        result = self.run_team("--from", "deploy")
        self.assertEqual(result.returncode, 10, result.stdout + result.stderr)
        self.assertIn("unknown stage for --from", result.stderr)

    def test_unknown_option_is_rejected(self):
        result = self.run_team("--fast")
        self.assertEqual(result.returncode, 10, result.stdout + result.stderr)
        self.assertIn("unknown option", result.stderr)

    def test_missing_repository_is_rejected(self):
        result = subprocess.run(
            ["bash", str(RUNNER), str(self.tmp / "nope"), "--spec", "odd/tasks/demo.md"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 10)
        self.assertIn("not a directory", result.stderr)


if __name__ == "__main__":
    unittest.main()

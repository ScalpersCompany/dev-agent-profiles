import json
import re
import unittest
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1]
ROLES = ("plan", "dev", "review", "verify", "judge")


class TestProfileContract(unittest.TestCase):
    def test_profile_paths_exist(self):
        data = json.loads((PROFILE / "profile.json").read_text(encoding="utf-8"))
        self.assertRegex(data["name"], r"^[a-z][a-z0-9-]*$")
        self.assertRegex(data["version"], r"^[0-9]+\.[0-9]+\.[0-9]+$")
        self.assertEqual(data["api"], 1)
        for key in ("verify", "skills", "evals", "agents"):
            self.assertTrue((PROFILE / data[key]).exists(), key)
        for guard in data["guard"]:
            self.assertTrue((PROFILE / guard).is_file(), guard)
        self.assertTrue((PROFILE / "gga" / "REVIEW-RULES.md").is_file())

    def test_env_matches_profile(self):
        data = json.loads((PROFILE / "profile.json").read_text(encoding="utf-8"))
        env = {}
        for line in (PROFILE / "profile.env").read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
        self.assertEqual(env["PROFILE_NAME"], data["name"])
        self.assertEqual(env["PROFILE_GUARD_CHECKS"], data["guard"][0])
        self.assertEqual(env["PROFILE_VERIFY_CONFIG"], "verify/config.env")
        self.assertTrue(re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", data["version"]))

    def test_roles_cover_every_stage_once(self):
        data = json.loads((PROFILE / "roles.json").read_text(encoding="utf-8"))
        names = [role["role"] for role in data["roles"]]
        self.assertEqual(sorted(names), sorted(ROLES))
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(data["profile"], "team")
        self.assertEqual(data["handoff"], "task-file-reference")

    def test_only_dev_owns_the_worktree(self):
        data = json.loads((PROFILE / "roles.json").read_text(encoding="utf-8"))
        owners = [role["role"] for role in data["roles"] if role["owns_worktree"]]
        self.assertEqual(owners, ["dev"])
        writers = [role["role"] for role in data["roles"] if role["writes"]]
        self.assertEqual(sorted(writers), ["dev", "plan"])

    def test_readonly_roles_write_nothing_on_a_copy(self):
        data = json.loads((PROFILE / "roles.json").read_text(encoding="utf-8"))
        for role in data["roles"]:
            if role["role"] in ("review", "verify", "judge"):
                self.assertTrue(role["readonly"], role["role"])
                self.assertTrue(role["runs_on_copy"], role["role"])
                self.assertEqual(role["writes"], [], role["role"])

    def test_placeholders_are_declared(self):
        data = json.loads((PROFILE / "roles.json").read_text(encoding="utf-8"))
        declared = set(data["placeholders"])
        used = set()
        for role in data["roles"]:
            values = list(role["writes"]) + list(role["reads"]) + [role["entry"]]
            values += [item["command"] for item in role["exit"]]
            for value in values:
                used.update(re.findall(r"\{[a-z][a-z0-9_]*\}", value))
        self.assertEqual(used - declared, set())

    def test_exit_commands_are_set(self):
        data = json.loads((PROFILE / "roles.json").read_text(encoding="utf-8"))
        for role in data["roles"]:
            self.assertTrue(role["exit"], role["role"])
            for item in role["exit"]:
                self.assertTrue(item["command"].strip(), role["role"])
                self.assertTrue(item["expect"].strip(), role["role"])
            self.assertIn("git push", role["forbidden"], role["role"])

    def test_roles_document_names_every_role(self):
        text = (PROFILE / "roles.md").read_text(encoding="utf-8")
        for role in ROLES:
            self.assertIn("`%s`" % role, text)


if __name__ == "__main__":
    unittest.main()

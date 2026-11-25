import json
import re
import unittest
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()

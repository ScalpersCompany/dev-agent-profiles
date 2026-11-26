#!/usr/bin/env python3
"""Role contract checks for the team profile."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REQUIRED_ROLES = ("plan", "dev", "review", "verify", "judge")
READONLY_ROLES = ("review", "verify", "judge")
ROLE_KEYS = (
    "role",
    "stage",
    "writes",
    "reads",
    "readonly",
    "runs_on_copy",
    "owns_worktree",
    "entry",
    "exit",
    "forbidden",
)
EXIT_KEYS = ("command", "expect")
ALLOWED_COMMANDS = (
    "dev-agent ",
    "bash verify/run.sh",
    "python3 .dev-agent/profiles/team/guard/team_lint.py",
)
PLACEHOLDER_RE = re.compile(r"\{[a-z][a-z0-9_]*\}")
SPEC_RE = re.compile(r"\bS(\d+)\b")
TASK_ROW_BULLET = re.compile(r"^\s*[-*]\s*\**T(\d+)\b")
TASK_ROW_TABLE = re.compile(r"^\s*\|\s*\**T(\d+)\b")
TASK_HEADINGS = ("## Specs", "## Tasks", "## Log")


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, "missing %s" % path.name
    except json.JSONDecodeError as exc:
        return None, "invalid %s: %s" % (path.name, exc)


def check_glob(value, placeholders, errors, label):
    if not isinstance(value, str) or not value.strip():
        errors.append("%s must be a non-empty string" % label)
        return
    if value.startswith("/") or ".." in Path(value).parts:
        errors.append("%s escapes the repository: %s" % (label, value))
    for token in PLACEHOLDER_RE.findall(value):
        if token not in placeholders:
            errors.append("%s uses an undeclared placeholder: %s" % (label, token))


def check_exit(role, command_errors):
    for index, item in enumerate(role.get("exit", [])):
        label = "%s.exit[%d]" % (role["role"], index)
        if not isinstance(item, dict):
            command_errors.append("%s must be an object" % label)
            continue
        for key in EXIT_KEYS:
            if not isinstance(item.get(key), str) or not item.get(key, "").strip():
                command_errors.append("%s missing %s" % (label, key))
        command = item.get("command", "")
        if command and not command.startswith(ALLOWED_COMMANDS):
            command_errors.append(
                "%s is outside the kit command list: %s" % (label, command)
            )
        expect = item.get("expect", "")
        if role["role"] == "review" and expect and "STATUS: PASSED" not in expect:
            command_errors.append("%s must require STATUS: PASSED" % label)
        if role["role"] != "review" and expect and "exit 0" not in expect:
            command_errors.append("%s must require exit 0" % label)


def contract_errors(profile_dir):
    errors = []
    profile, problem = load_json(profile_dir / "profile.json")
    if problem:
        errors.append(problem)
        profile = {}
    if not isinstance(profile, dict):
        errors.append("profile.json must be a JSON object")
        profile = {}
    data, problem = load_json(profile_dir / "roles.json")
    if problem:
        errors.append(problem)
        return errors
    if not isinstance(data, dict):
        return errors + ["roles.json must be a JSON object"]
    if data.get("api") != 1:
        errors.append("roles.json api must be 1")
    if data.get("profile") != profile.get("name"):
        errors.append("roles.json profile does not match profile.json name")
    if data.get("handoff") != "task-file-reference":
        errors.append("roles.json handoff must be task-file-reference")
    placeholders = data.get("placeholders")
    if not isinstance(placeholders, list) or not placeholders:
        errors.append("roles.json placeholders must be a non-empty list")
        placeholders = []
    for token in placeholders:
        if not isinstance(token, str) or not PLACEHOLDER_RE.fullmatch(token):
            errors.append("invalid placeholder: %s" % token)
    declared = set(placeholders)

    roles = data.get("roles")
    if not isinstance(roles, list):
        return errors + ["roles.json roles must be a list"]
    names = [str(role.get("role")) for role in roles if isinstance(role, dict)]
    if sorted(names) != sorted(REQUIRED_ROLES):
        errors.append("roles must be exactly %s" % ", ".join(REQUIRED_ROLES))
    owners = [
        str(role.get("role"))
        for role in roles
        if isinstance(role, dict) and role.get("owns_worktree")
    ]
    if owners != ["dev"]:
        errors.append("dev must be the only role that owns the worktree")

    for role in roles:
        if not isinstance(role, dict):
            errors.append("every role must be an object")
            continue
        name = role.get("role", "?")
        for key in ROLE_KEYS:
            if key not in role:
                errors.append("%s missing key: %s" % (name, key))
        if role.get("readonly"):
            if name not in READONLY_ROLES:
                errors.append("%s cannot be read-only" % name)
            if not role.get("runs_on_copy"):
                errors.append("%s is read-only and must run on a copy" % name)
            if role.get("writes"):
                errors.append("%s is read-only and declares writes" % name)
            if role.get("owns_worktree"):
                errors.append("%s is read-only and cannot own the worktree" % name)
        writes = role.get("writes")
        if not isinstance(writes, list):
            errors.append("%s writes must be a list" % name)
            writes = []
        for value in writes:
            check_glob(value, declared, errors, "%s.writes" % name)
        reads = role.get("reads")
        if not isinstance(reads, list):
            errors.append("%s reads must be a list" % name)
            reads = []
        for value in reads:
            check_glob(value, declared, errors, "%s.reads" % name)
        if name == "plan":
            if not writes or any(not item.startswith("odd/tasks/") for item in writes):
                errors.append("plan writes only under odd/tasks/")
        if name == "dev":
            if not writes or any(not item.startswith("addons/") for item in writes):
                errors.append("dev writes only under addons/")
            if not role.get("owns_worktree"):
                errors.append("dev must own the worktree")
        entry = role.get("entry")
        if not isinstance(entry, str) or not entry.startswith(ALLOWED_COMMANDS):
            errors.append("%s.entry is outside the kit command list" % name)
        else:
            for token in PLACEHOLDER_RE.findall(entry):
                if token not in declared:
                    errors.append("%s.entry uses an undeclared placeholder: %s" % (name, token))
        forbidden = role.get("forbidden")
        if not isinstance(forbidden, list) or "git push" not in forbidden:
            errors.append("%s must forbid git push" % name)
        if not isinstance(role.get("exit"), list) or not role.get("exit"):
            errors.append("%s must declare at least one exit command" % name)
        else:
            check_exit(role, errors)

    doc = profile_dir / "roles.md"
    if not doc.is_file():
        errors.append("missing roles.md")
    else:
        text = doc.read_text(encoding="utf-8")
        for name in REQUIRED_ROLES:
            if "`%s`" % name not in text:
                errors.append("roles.md does not document the role: %s" % name)
    return errors


def section_lines(text, heading):
    lines = text.splitlines()
    try:
        start = [line.strip() for line in lines].index(heading)
    except ValueError:
        return None
    body = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped in TASK_HEADINGS or stripped.startswith("## "):
            break
        body.append(line)
    return body


def task_errors(path):
    if not path.is_file():
        return ["missing task file: %s" % path]
    text = path.read_text(encoding="utf-8")
    errors = []
    specs = section_lines(text, "## Specs")
    tasks = section_lines(text, "## Tasks")
    log = section_lines(text, "## Log")
    for heading, body in (("## Specs", specs), ("## Tasks", tasks), ("## Log", log)):
        if body is None:
            errors.append("task file missing heading: %s" % heading)
    if specs is None or tasks is None or log is None:
        return errors
    spec_ids = set()
    for line in specs:
        spec_ids.update(SPEC_RE.findall(line))
    if not spec_ids:
        errors.append("task file has no S# spec")
    for line in tasks:
        row = TASK_ROW_BULLET.match(line) or TASK_ROW_TABLE.match(line)
        if row is None:
            continue
        number = row.group(1)
        cited = set(SPEC_RE.findall(line))
        if not cited:
            if "—" in line or "sin spec" in line.lower():
                continue
            errors.append("task T%s without an S# reference: %s" % (number, line.strip()[:60]))
            continue
        unknown = sorted(cited - spec_ids)
        if unknown:
            errors.append(
                "task T%s cites an unknown spec: %s"
                % (number, ", ".join("S" + item for item in unknown))
            )
    first = next((line.strip() for line in log if line.strip()), "")
    if not re.match(r"^(- )?L1\b", first):
        errors.append("log must start with L1, the verbatim request")
    return errors


def evidence_errors(directory):
    summary = directory / "summary.json"
    data, problem = load_json(summary)
    if problem:
        return [problem]
    if not isinstance(data, dict):
        return ["summary.json must be a JSON object"]
    errors = []
    for key in ("run_id", "sha"):
        if not str(data.get(key) or "").strip():
            errors.append("summary.json %s is empty" % key)
    if data.get("status") != "pass":
        errors.append("summary.json status is %s" % data.get("status"))
    if data.get("tests") != "pass":
        errors.append("summary.json tests is %s" % data.get("tests"))
    e2e = data.get("e2e")
    if e2e not in ("pass", "skipped"):
        errors.append("summary.json e2e is %s" % e2e)
    ran = [data.get(key) == "pass" for key in ("smoke", "tests", "e2e")]
    if not any(ran):
        errors.append("no check ran: smoke, tests and e2e are not pass")
    return errors


def score_errors(path):
    data, problem = load_json(path)
    if problem:
        return [problem]
    if not isinstance(data, dict):
        return ["score.json must be a JSON object"]
    errors = []
    try:
        runs = int(data.get("k") or 0)
    except (TypeError, ValueError):
        runs = 0
    if runs < 3:
        errors.append("score.json k is %s, at least 3 runs required" % data.get("k"))
    if data.get("passed") is not True:
        errors.append("score.json passed is not true")
    raw_aggregate = data.get("aggregate")
    aggregate = raw_aggregate if isinstance(raw_aggregate, dict) else {}
    mean_value = aggregate.get("mean")
    threshold_value = data.get("threshold")
    if mean_value is None or threshold_value is None:
        return errors + ["score.json has no numeric mean and threshold"]
    try:
        mean = float(mean_value)
        threshold = float(threshold_value)
    except (TypeError, ValueError):
        return errors + ["score.json has no numeric mean and threshold"]
    if mean < threshold:
        errors.append("score.json mean %s is below threshold %s" % (mean, threshold))
    model = str(data.get("model") or "").strip()
    judge = str(data.get("judge_model") or "").strip()
    if not model or not judge:
        errors.append("score.json must name model and judge_model")
    elif model == judge:
        errors.append("score.json judge_model equals model")
    return errors


def tree_hash(path):
    head = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if head.returncode != 0:
        return None, "not a git worktree: %s" % path
    status = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if status.returncode != 0:
        return None, "git status failed in %s" % path
    payload = head.stdout.strip() + "\n" + status.stdout
    return hashlib.sha256(payload.encode("utf-8")).hexdigest(), None


def main():
    parser = argparse.ArgumentParser(description="Check the team role contract")
    parser.add_argument(
        "--profile",
        default=str(Path(__file__).resolve().parents[1]),
        help="profile directory",
    )
    parser.add_argument("--task", help="task file to check")
    parser.add_argument("--evidence", help="evidence run directory to certify")
    parser.add_argument("--score", help="eval score.json to certify")
    parser.add_argument("--tree-snapshot", help="print the hash of a worktree")
    parser.add_argument(
        "--tree-unchanged",
        nargs=2,
        metavar=("TREE", "HASH"),
        help="fail when the worktree no longer matches the hash",
    )
    args = parser.parse_args()

    if args.tree_snapshot:
        digest, problem = tree_hash(Path(args.tree_snapshot))
        if problem:
            print("error: %s" % problem, file=sys.stderr)
            return 2
        print(digest)
        return 0

    if args.tree_unchanged:
        tree, expected = args.tree_unchanged
        digest, problem = tree_hash(Path(tree))
        if problem:
            print("error: %s" % problem, file=sys.stderr)
            return 2
        if digest != expected.strip():
            print("error: tree changed: %s != %s" % (digest, expected), file=sys.stderr)
            return 1
        print("ok: tree unchanged")
        return 0

    errors = contract_errors(Path(args.profile))
    if args.task:
        errors.extend(task_errors(Path(args.task)))
    if args.evidence:
        errors.extend(evidence_errors(Path(args.evidence)))
    if args.score:
        errors.extend(score_errors(Path(args.score)))
    if errors:
        for error in errors:
            print("error: %s" % error, file=sys.stderr)
        return 1
    print("ok: %s" % Path(args.profile).resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())

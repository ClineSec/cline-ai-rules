#!/usr/bin/env python3
"""Scan every testbed with the built rule pack and compare against its expectations.

Each testbed under testbeds/<name>/ has an expectations.yaml listing every finding the pack
must produce there. A missing finding is a false negative, an unlisted finding is a false
positive, and both fail. Every rule in rules.yaml must be exercised by at least one testbed.

Every file an expectation names must also be in git's index (committed or staged): the scan
reads the working tree, so an untracked or git-ignored file (a global gitignore often ignores
.claude/settings.local.json) would pass here and be missing from a fresh checkout.

Each testbed is scanned twice: in OpenGrep's default mode, and with --taint-intrafile
(cross-function taint within a file). Expectations marked `requires: taint-intrafile` are only
expected in the second scan, which documents what default-mode users miss.

Usage:
    python3 scripts/testbeds.py                 # all testbeds
    python3 scripts/testbeds.py py-helpdesk     # one testbed (skips the coverage check)
    python3 scripts/testbeds.py --rule my-rule  # only my-rule's findings, in every testbed
    python3 scripts/testbeds.py --jobs 4        # cap OpenGrep at 4 cores (default: all)

A full run scans every testbed twice with every rule and keeps several cores busy for minutes.
While building a rule, check it alone with --rule (repeatable; run build.py first so rules.yaml
has it) and --jobs 4; run the full check once before committing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TESTBEDS = ROOT / "testbeds"
RULES = ROOT / "rules.yaml"


def load_expectations(bed: Path, rules: set[str] | None = None) -> list[dict]:
    doc = yaml.safe_load((bed / "expectations.yaml").read_text()) or {}
    found = doc.get("findings") or []
    return found if rules is None else [e for e in found if e.get("rule") in rules]


MODES = {"default": [], "taint-intrafile": ["--taint-intrafile"]}


def scan(bed: Path, config: Path, extra: list[str]) -> dict:
    proc = subprocess.run(
        ["opengrep", "scan", "--config", str(config), "--json", "--quiet",
         "--disable-version-check", "--no-git-ignore", *extra, "."],
        cwd=bed, capture_output=True, text=True,
    )
    if proc.returncode not in (0, 1):
        raise SystemExit(f"opengrep failed on {bed.name}:\n{proc.stderr}")
    return json.loads(proc.stdout)


def anchor_lines(bed: Path, rel: str, needle: str) -> list[int]:
    path = bed / rel
    if not path.is_file():
        return []
    return [i for i, line in enumerate(path.read_text().splitlines(), 1) if needle in line]


def git_index() -> set[str] | None:
    # Paths (relative to the repo root) in git's index, so staged new files count; None when
    # this isn't a git checkout.
    proc = subprocess.run(["git", "ls-files", "-z", "--", "testbeds"], cwd=ROOT,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return set(proc.stdout.split("\0")) - {""}


def check_tracked(bed: Path, index: set[str], rules: set[str] | None,
                  problems: list[str]) -> None:
    for rel in sorted({e.get("file") for e in load_expectations(bed, rules) if e.get("file")}):
        path = (bed / rel).relative_to(ROOT).as_posix()
        if path in index:
            continue
        ignored = subprocess.run(["git", "check-ignore", "-q", "--no-index", "--", path],
                                 cwd=ROOT).returncode == 0
        why = ("git-ignored (git add -f it, or move the finding to a file git keeps)" if ignored
               else "not in git's index (git add it)")
        problems.append(f"{bed.name}: NOT COMMITTED {rel}: {why}; a fresh checkout would not have this file")


def check_bed(bed: Path, mode: str, config: Path, rules: set[str] | None, extra: list[str],
              problems: list[str]) -> set[str]:
    label = f"{bed.name} [{mode}]"
    expectations = [
        e for e in load_expectations(bed, rules)
        if mode == "taint-intrafile" or e.get("requires") != "taint-intrafile"
    ]
    result = scan(bed, config, MODES[mode] + extra)
    for err in result.get("errors", []):
        problems.append(f"{label}: opengrep error: {err.get('message', err)}".strip())

    findings = [
        # OpenGrep prefixes rule IDs with the config's path; rule IDs never contain dots.
        {"rule": r["check_id"].rsplit(".", 1)[-1], "file": r["path"].removeprefix("./"),
         "start": r["start"]["line"], "end": r["end"]["line"], "claimed": False}
        for r in result.get("results", [])
    ]
    exercised = set()
    for exp in expectations:
        rule, rel, needle = exp.get("rule"), exp.get("file"), exp.get("line_contains")
        if not (rule and rel and needle):
            problems.append(f"{label}: expectation needs rule, file, and line_contains: {exp}")
            continue
        lines = anchor_lines(bed, rel, needle)
        if not lines:
            problems.append(f"{label}: anchor not found: {rel}: {needle!r} ({rule})")
            continue
        hits = [f for f in findings
                if f["rule"] == rule and f["file"] == rel
                and any(f["start"] <= ln <= f["end"] for ln in lines)]
        if not hits:
            problems.append(f"{label}: MISSED {rule} at {rel}: {needle!r}")
            continue
        for f in hits:
            f["claimed"] = True
        exercised.add(rule)

    for f in findings:
        if not f["claimed"]:
            text = (bed / f["file"]).read_text().splitlines()[f["start"] - 1].strip()
            problems.append(f"{label}: UNEXPECTED {f['rule']} at {f['file']}:{f['start']}: {text[:100]}")
    return exercised


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the testbeds against their expectations.")
    parser.add_argument("testbeds", nargs="*", help="testbed names (default: all)")
    parser.add_argument("--rule", action="append", dest="rules", metavar="ID",
                        help="check only this rule's findings (repeatable)")
    parser.add_argument("--jobs", type=int, metavar="N", help="cores OpenGrep may use")
    args = parser.parse_args()

    if not RULES.exists():
        raise SystemExit("rules.yaml is missing; run python3 scripts/build.py first")
    wanted = args.testbeds
    rules = set(args.rules) if args.rules else None
    extra = ["--jobs", str(args.jobs)] if args.jobs else []
    config = RULES
    if rules is not None:
        pack = yaml.safe_load(RULES.read_text())["rules"]
        unknown = rules - {r["id"] for r in pack}
        if unknown:
            raise SystemExit(f"not in rules.yaml (run python3 scripts/build.py?): "
                             f"{', '.join(sorted(unknown))}")
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        yaml.safe_dump({"rules": [r for r in pack if r["id"] in rules]}, tmp, sort_keys=False)
        tmp.close()
        config = Path(tmp.name)
    beds = sorted(p for p in TESTBEDS.iterdir() if (p / "expectations.yaml").is_file())
    if wanted:
        beds = [b for b in beds if b.name in wanted]
        missing = set(wanted) - {b.name for b in beds}
        if missing:
            raise SystemExit(f"unknown testbed(s): {', '.join(sorted(missing))}")

    problems: list[str] = []
    exercised: set[str] = set()
    index = git_index()
    if index is None:
        print("warning: not a git checkout; skipping the committed-file check", file=sys.stderr)
    try:
        for bed in beds:
            if index is not None:
                check_tracked(bed, index, rules, problems)
            for mode in MODES:
                exercised |= check_bed(bed, mode, config, rules, extra, problems)
    finally:
        if config != RULES:
            config.unlink()

    if not wanted:
        rule_ids = rules or {r["id"] for r in yaml.safe_load(RULES.read_text())["rules"]}
        for rule in sorted(rule_ids - exercised):
            problems.append(f"coverage: rule {rule} has no expected finding in any testbed")

    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"ok: {len(beds)} testbed(s) match expectations; {len(exercised)} rule(s) exercised")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Measure how strong the per-unit differential harness is.

For every accepted unit of a completed unit-engine run, apply single
first-order mutation operators to the accepted Rust function, keep mutants
that still compile, and re-run the unit's differential test. A mutant is
"killed" if the harness rejects it. Surviving mutants are listed for manual
inspection: some may be semantically equivalent to the original.

Usage: scripts/harness_mutation_check.py RUN_DIR [--cases N] [--max-mutants K]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from safemap.models import CAnalysis, MigrationPlan, ProjectInfo, from_dict  # noqa: E402
from safemap.process import run_command  # noqa: E402
from safemap.validation.unit_harness import validate_units  # noqa: E402

OPERATORS = (
    ("relational", r"(?<=\s)==(?=\s)", "!="),
    ("relational", r"(?<=\s)!=(?=\s)", "=="),
    ("relational", r"(?<=\s)<=(?=\s)", "<"),
    ("relational", r"(?<=\s)>=(?=\s)", ">"),
    ("relational", r"(?<=\s)<(?=\s)", "<="),
    ("relational", r"(?<=\s)>(?=\s)", ">="),
    ("arithmetic", r"(?<=\s)\+(?=\s)", "-"),
    ("arithmetic", r"(?<=\s)-(?=\s)", "+"),
    ("logical", r"&&", "||"),
    ("logical", r"\|\|", "&&"),
    ("boolean", r"\btrue\b", "false"),
    ("boolean", r"\bfalse\b", "true"),
    ("literal", r"(?<![\w.])(\d+)(?![\w.])", None),
)


def mutants(function: str, limit: int) -> list[tuple[str, str]]:
    head, brace, body = function.partition("{")
    found = []
    for kind, pattern, replacement in OPERATORS:
        for match in re.finditer(pattern, body):
            new = str(int(match.group(1)) + 1) if replacement is None else replacement
            mutated = body[:match.start()] + new + body[match.end():]
            found.append((f"{kind}:{match.group(0)}->{new}@{match.start()}", head + brace + mutated))
    # Spread the budget across operators rather than taking the first K.
    found.sort(key=lambda item: (hashlib.sha256(item[0].encode()).hexdigest(), item[0]))
    return found[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--cases", type=int, default=300)
    parser.add_argument("--max-mutants", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run = args.run_dir.resolve()
    project = from_dict(ProjectInfo, json.loads((run / "project.json").read_text()))
    analysis = from_dict(CAnalysis, json.loads((run / "analysis/c_analysis.json").read_text()))
    plans = [from_dict(MigrationPlan, json.loads(path.read_text())) for path in sorted((run / "plans").glob("*.json"))]
    metrics = json.loads((run / "reports/metrics.json").read_text())
    accepted = metrics.get("fully_safe_accepted_unit_ids", [])
    crate = run / "final" / "rust"
    lib = (crate / "src" / "lib.rs").read_text(encoding="utf-8")
    report = {"run": str(run), "cases": args.cases, "units": []}
    for unit_id in accepted:
        outcome = json.loads((run / "synthesis" / f"{unit_id}.json").read_text())
        original = outcome["rust_code"]
        entry = {"unit_id": unit_id, "function": outcome["function"], "mutants": []}
        for label, code in mutants(original, args.max_mutants):
            with tempfile.TemporaryDirectory(prefix="safemap-mutant-") as temp:
                copy = Path(temp) / "crate"
                shutil.copytree(crate, copy, ignore=shutil.ignore_patterns("target"))
                (copy / "src" / "lib.rs").write_text(lib.replace(original, code), encoding="utf-8")
                check = run_command(["cargo", "check", "--quiet"], copy, timeout=300)
                if check.status != "passed":
                    entry["mutants"].append({"mutant": label, "result": "stillborn"})
                    continue
                result = validate_units(
                    Path(project.c_files[0]), copy, Path(temp) / "work",
                    analysis.functions, plans, analysis.structs, [unit_id],
                    cases=args.cases, seed=1,
                )[unit_id]
                # Only an observed output mismatch is a kill; a harness or
                # oracle problem says nothing about the harness's strength.
                verdict = {"passed": "survived", "failed": "killed"}.get(result.status, "invalid")
                entry["mutants"].append({
                    "mutant": label, "result": verdict, "status": result.status,
                })
        live = [item for item in entry["mutants"] if item["result"] in {"killed", "survived"}]
        entry["killed"] = sum(item["result"] == "killed" for item in live)
        entry["compiled_mutants"] = len(live)
        report["units"].append(entry)
        print(f"{entry['function']:28} killed {entry['killed']}/{entry['compiled_mutants']}", flush=True)
    killed = sum(item["killed"] for item in report["units"])
    total = sum(item["compiled_mutants"] for item in report["units"])
    report["killed"], report["compiled_mutants"] = killed, total
    report["mutation_score"] = killed / total if total else None
    print(f"TOTAL killed {killed}/{total}")
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

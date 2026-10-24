#!/usr/bin/env python3
"""Generate the v2 manuscript tables (LaTeX) from evaluation checkpoints.

Usage: scripts/generate_v2_manuscript_tables.py HELDOUT_ROOT DEV_ROOT OUT_DIR

HELDOUT_ROOT holds the v2 stage directories (v2-non-llm, v2-llm, v2-ablation,
ext/..., rep2-orig/..., ...); DEV_ROOT holds the development corpora.
Every number in the tables is read from benchmark_results.rows.jsonl files,
and the amendment-3 (per-unit Clippy) numbers from HELDOUT_ROOT/amendment3
(scripts/rescore_per_unit_clippy.py). Where amendment 3 changes a number, the
sealed number follows in parentheses.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from safemap.pipeline import UNIT_FAILURE_CATEGORY  # noqa: E402

ORIG = ("microtar", "parson", "sds", "tinyexpr")
EXT = ("argparse", "json-parser", "printf", "semver", "tiny-AES-c", "tiny-regex-c")
ACCEPTED = "fully_safe_accepted_units"
# Unit statuses that mean the unit passed every crate-level check.
PAST_CRATE = {"accepted", "failed", "insufficient_defined_inputs", "not_harnessable",
              "harness_build_failed", "c_oracle_timeout"}
RUN_STAGES = {1: ("v2-llm", "ext/v2-llm", "v2-non-llm", "ext/v2-non-llm", "plain-orig", "plain-ext")}
RUN_STAGES.update({i: (f"rep{i}-orig/v2-llm", f"rep{i}-ext/v2-llm", f"plain-rep{i}-orig",
                       f"plain-rep{i}-ext") for i in (2, 3)})


def amendment3(held: Path) -> dict[int, dict[tuple[str, str], dict]]:
    """Per-unit Clippy results, keyed like load(): run -> (library, mode) -> result."""
    runs: dict[int, dict] = {i: {} for i in RUN_STAGES}
    for item in json.loads((held / "amendment3/rescore.json").read_text(encoding="utf-8")):
        run = next(i for i, stages in RUN_STAGES.items() if item["stage"] in stages)
        mode = "llm_plain" if item["stage"].startswith("plain") else item["mode"]
        name = "microtar" if item["project"] == "src" else item["project"]
        runs[run][(name, mode)] = item
    return runs


def cell(new: int, old: int) -> str:
    return str(new) if new == old else f"{new} ({old})"


def _name(row: dict) -> str:
    # microtar's sources live in src/, so its project directory is "src".
    name = Path(row["project"]).name
    return "microtar" if name == "src" else name


def load(*stage_dirs: Path) -> dict[tuple[str, str], dict]:
    rows = {}
    for stage in stage_dirs:
        path = stage / "benchmark_results.rows.jsonl"
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)["row"]
            rows[(_name(row), row["mode"])] = row
    return rows


def n(row: dict | None, key: str) -> int:
    return int((row or {}).get(key) or 0)


def table(caption: str, label: str, header: list[str], body: list[list], align: str) -> str:
    lines = [r"\begin{table}[t]", r"\centering", rf"\caption{{{caption}}}", rf"\label{{{label}}}",
             r"\scriptsize", rf"\begin{{tabular}}{{{align}}}", r"\toprule", " & ".join(header) + r" \\",
             r"\midrule"]
    for row in body:
        lines.append(r"\midrule" if row == "---" else " & ".join(str(c) for c in row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lines)


def corpus_table(rows: dict) -> str:
    body, total = [], Counter()
    for group, names in (("Original", ORIG), ("Extension", EXT)):
        for name in names:
            r = rows.get((name, "safemap_deterministic"))
            if not r:
                continue
            vals = [n(r, "loc_c"), n(r, "c_function_count"), n(r, "total_units"),
                    n(r, "c_pointer_parameter_count"), n(r, "c_cyclomatic_complexity_total")]
            total.update(dict(zip("abcde", vals)))
            body.append([name, group, *vals])
        body.append("---")
    body.append(["Total", "", *(total[k] for k in "abcde")])
    return table("Held-out corpus: ten libraries from two selection rounds.", "tab:v2-corpus",
                 ["Library", "Round", "C LOC", "Functions", "Units", "Ptr. params", "Complexity"],
                 body, "llrrrrr")


def cascade_table(rows: dict, a3: dict) -> str:
    keys = ("total_units", "candidate_safe_units", "generated_units", "compile_success_units",
            "policy_safe_units", ACCEPTED)
    body, total, old = [], Counter(), Counter()
    for name in ORIG + EXT:
        r = rows.get((name, "safemap_guided"))
        if not r:
            continue
        sealed = [n(r, k) for k in keys]
        outcomes = a3[(name, "safemap_guided")]["outcomes"].values()
        crate = sum(status in PAST_CRATE for status in outcomes)
        vals = [*sealed[:3], crate, crate, a3[(name, "safemap_guided")]["per_unit_clippy_accepted"]]
        if sealed[3] != 0 and sealed[3] != crate:
            raise SystemExit(f"{name}: derived crate count {crate} != archived {sealed[3]}")
        total.update(dict(enumerate(vals)))
        old.update(dict(enumerate(sealed)))
        body.append([name, *(cell(v, o) for v, o in zip(vals, sealed))])
        if name == ORIG[-1]:
            body.append("---")
    body += ["---", ["Total", *(cell(total[i], old[i]) for i in range(6))]]
    return table(r"\tool (guided) outcome cascade per library (first run, per-unit Clippy; sealed "
                 r"result in parentheses where it differs). \emph{Crate}: the unit passed \texttt{cargo "
                 r"check} and tests, and Clippy found no error in it or in its callees.", "tab:v2-cascade",
                 ["Library", "Units", "Candidate", "Generated", "Crate", "Policy", "Accepted"],
                 body, "lrrrrrr")


def _failures(row: dict) -> dict:
    value = row.get("failure_categories") or {}
    return json.loads(value) if isinstance(value, str) else value


def baseline_table(rows: dict, a3: dict) -> str:
    modes = ("safemap_guided", "llm_only", "llm_plain", "safemap_deterministic", "c2rust_only")
    body, total, old = [], Counter(), Counter()
    for name in ORIG + EXT:
        if (name, "safemap_guided") not in rows:
            continue
        units = n(rows.get((name, "safemap_guided")), "total_units")
        sealed = [n(rows.get((name, m)), ACCEPTED) for m in modes[:4]]
        new = [a3[(name, m)]["per_unit_clippy_accepted"] for m in modes[:4]]
        vals = [cell(v, o) for v, o in zip(new, sealed)] + [n(rows.get((name, "c2rust_only")), ACCEPTED)]
        c2r = rows.get((name, "c2rust_only")) or {}
        if str(c2r.get("c2rust_compile")) != "True":
            vals[-1] = f"{vals[-1]}$^\\dagger$"
        calls = [n(rows.get((name, m)), "llm_calls") for m in modes[:2]]
        total.update({"u": units, **dict(zip(modes[:4], new)), "cg": calls[0], "cl": calls[1]})
        old.update(dict(zip(modes[:4], sealed)))
        body.append([name, units, *vals, f"{calls[0]} / {calls[1]}"])
        if name == ORIG[-1]:
            body.append("---")
    body += ["---", ["Total", total["u"], *(cell(total[m], old[m]) for m in modes[:4]), 0,
                     f"{total['cg']} / {total['cl']}"]]
    return table("Accepted units per configuration on the held-out libraries (first run, per-unit "
                 "Clippy, amendment 3; sealed result in parentheses where it differs). "
                 "One-shot: given the planned signatures; plain: C sources only (amendment 2). "
                 "LLM calls: guided / one-shot. $^\\dagger$C2Rust output did not compile.",
                 "tab:v2-baselines",
                 ["Library", "Units", "Guided", "One-shot", "Plain", "Rules", "C2Rust", "LLM calls"],
                 body, "lrrrrrrr")


def refusal_table(rows: dict, a3: dict, reasons: dict) -> str:
    # Screening decisions are unchanged by amendment 3; later outcomes come from it.
    counts = Counter({k: reasons[k] for k in ("unresolved_pointer_ownership", "global_state")})
    sealed_total, gained = 0, 0
    for name in ORIG + EXT:
        r = rows.get((name, "safemap_guided"))
        if not r:
            continue
        failures = _failures(r)
        counts.update({k: failures.get(k, 0) for k in ("unsafe_required", "unsupported")})
        item = a3[(name, "safemap_guided")]
        counts.update(UNIT_FAILURE_CATEGORY.get(s, s) for s in item["outcomes"].values() if s != "accepted")
        sealed_total += sum(failures.values())
        gained += item["per_unit_clippy_accepted"] - n(r, ACCEPTED)
    # Every newly accepted unit must leave exactly one refusal behind.
    if sum(counts.values()) != sealed_total - gained:
        raise SystemExit(f"refusals sum to {sum(counts.values())}, expected {sealed_total - gained}")
    labels = {
        "unresolved_pointer_ownership": "Manual refactor: pointer ownership or aliasing unresolved",
        "global_state": "Manual refactor: mutable global state",
        "clippy_failed": "Clippy error in the unit or a callee",
        "type_mapping_unresolved": "No safe, testable interface for a C type",
        "unsafe_required": "Requires unsafe (raw memory, casts)",
        "unsupported": "Unsupported construct (union, function pointer, asm)",
        "dependency_not_translated": "Callee not translated",
        "dependency_missing": "Callee not translated",
        "behavior_mismatch": "Differential test failed",
        "validation_failed": "Crate-level Clippy check failed",
        "c_oracle_undefined_behavior": "C undefined on most test inputs",
        "not_planned": "No synthesis plan",
        "not_harnessable": "No applicable differential harness",
        "compile_failed": "Did not compile",
        "llm_error": "LLM output rejected",
    }
    merged = Counter()
    for key, value in counts.items():
        merged[labels.get(key, key.replace("_", " "))] += value
    body = [[label, value] for label, value in merged.most_common()]
    return table(r"Recorded reasons for functions not accepted by \tool (guided), all ten held-out "
                 r"libraries (first run, per-unit Clippy).",
                 "tab:v2-refusals", ["Reason", "Functions"], body, "lr")


def repeat_table(runs: list[tuple[str, dict]], a3: dict) -> str:
    body = []
    for i, (label, rows) in enumerate(runs, start=1):
        cells = []
        for mode in ("safemap_guided", "llm_only", "llm_plain"):
            sealed = sum(n(rows.get((x, mode)), ACCEPTED) for x in ORIG + EXT)
            new = sum(r["per_unit_clippy_accepted"] for (x, m), r in a3[i].items() if m == mode)
            cells.append(cell(new, sealed))
        libs = sum(1 for x in ORIG + EXT if (x, "safemap_guided") in rows)
        body.append([label, libs, *cells])
    return table("Accepted units across repeated LLM runs (identical inputs and configuration), with "
                 "per-unit Clippy; sealed result in parentheses where it differs. "
                 "One-shot: given the planned signatures; plain: C sources only.",
                 "tab:v2-repeats", ["Run", "Libraries", "Guided", "One-shot", "Plain"], body, "lrrrr")


def ablation_table(rows: dict) -> str:
    modes = [("safemap_guided", "Full system"),
             ("safemap_guided_unguided_prompt", "Facts and plan withheld from prompt"),
             ("safemap_guided_without_pointer_roles", "Without pointer roles"),
             ("safemap_guided_without_safe_signatures", "Without safe signatures"),
             ("safemap_guided_without_dependency_grouping", "Without dependency grouping"),
             ("safemap_guided_without_idiom_plans", "Without idiom plans"),
             ("safemap_guided_without_validation_feedback", "Without compiler-feedback repair")]
    libs = ("cJSON", "inih", "libcsv")
    body = []
    for mode, label in modes:
        cells = []
        for lib in libs:
            r = rows.get((lib.lower(), mode))
            cells.append(f"{n(r, ACCEPTED)}/{n(r, 'total_units')}" if r else "--")
        calls = sum(n(rows.get((lib.lower(), mode)), "llm_calls") for lib in libs)
        body.append([label, *cells, calls])
    return table(r"Component ablations on the v1 libraries (development data): accepted / all units.",
                 "tab:v2-ablations", ["Configuration", *libs, "LLM calls"], body, "lrrrr")


def development_table(dev: Path) -> str:
    corpora = (("examples", "Microbenchmarks"), ("case_studies", "Authored modules"),
               ("llvm", "LLVM programs"), ("v1diag", "v1 libraries"))
    modes = ("safemap_guided", "llm_only", "safemap_deterministic", "c2rust_only")
    body = []
    for key, label in corpora:
        rows = load(dev / key)
        units = sum(n(r, "total_units") for (_, m), r in rows.items() if m == "safemap_guided")
        body.append([label, units, *(sum(n(r, ACCEPTED) for (_, m), r in rows.items() if m == mode)
                                     for mode in modes)])
    return table("Development data: accepted units per configuration.", "tab:v2-development",
                 ["Corpus", "Units", "Guided", "One-shot LLM", "Rules only", "C2Rust"], body, "lrrrrr")


def main() -> None:
    held, dev, out = (Path(arg) for arg in sys.argv[1:4])
    out.mkdir(parents=True, exist_ok=True)
    def plain(*dirs: Path) -> dict:
        # Amendment 2: the plain baseline is recorded as llm_only in its own directories.
        return {(lib, "llm_plain"): row for (lib, _), row in load(*dirs).items()}

    first = load(held / "v2-non-llm", held / "v2-llm", held / "ext/v2-non-llm", held / "ext/v2-llm")
    first.update(plain(held / "plain-orig", held / "plain-ext"))
    repeats = [("Run 1", first)] + [
        (f"Run {i}", {**load(held / f"rep{i}-orig/v2-llm", held / f"rep{i}-ext/v2-llm"),
                      **plain(held / f"plain-rep{i}-orig", held / f"plain-rep{i}-ext")})
        for i in (2, 3)]
    ablation = load(held / "v2-ablation", held / "ablation-full")
    a3 = amendment3(held)
    reasons = json.loads((held / "amendment3/refactor_reasons.json").read_text(encoding="utf-8"))
    outputs = {
        "corpus.tex": corpus_table(first),
        "cascade.tex": cascade_table(first, a3[1]),
        "baselines.tex": baseline_table(first, a3[1]),
        "refusals.tex": refusal_table(first, a3[1], reasons),
        "repeats.tex": repeat_table(repeats, a3),
        "ablations.tex": ablation_table(ablation),
        "development.tex": development_table(dev),
    }
    for name, text in outputs.items():
        (out / name).write_text("% Generated by scripts/generate_v2_manuscript_tables.py; do not edit.\n"
                                + text, encoding="utf-8")
    print("wrote", ", ".join(outputs))


if __name__ == "__main__":
    main()

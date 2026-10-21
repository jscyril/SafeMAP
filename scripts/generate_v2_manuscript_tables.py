#!/usr/bin/env python3
"""Generate the v2 manuscript tables (LaTeX) from evaluation checkpoints.

Usage: scripts/generate_v2_manuscript_tables.py HELDOUT_ROOT DEV_ROOT OUT_DIR

HELDOUT_ROOT holds the v2 stage directories (v2-non-llm, v2-llm, v2-ablation,
ext/..., rep2-orig/..., ...); DEV_ROOT holds the development corpora.
Every number in the tables is read from benchmark_results.rows.jsonl files.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ORIG = ("microtar", "parson", "sds", "tinyexpr")
EXT = ("argparse", "json-parser", "printf", "semver", "tiny-AES-c", "tiny-regex-c")
ACCEPTED = "fully_safe_accepted_units"


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


def cascade_table(rows: dict) -> str:
    keys = ("total_units", "candidate_safe_units", "generated_units", "compile_success_units",
            "policy_safe_units", ACCEPTED)
    body, total = [], Counter()
    for name in ORIG + EXT:
        r = rows.get((name, "safemap_guided"))
        if not r:
            continue
        vals = [n(r, k) for k in keys]
        total.update(dict(enumerate(vals)))
        body.append([name, *vals])
        if name == ORIG[-1]:
            body.append("---")
    body += ["---", ["Total", *(total[i] for i in range(6))]]
    return table(r"\tool (guided) outcome cascade per library (first run). \emph{Crate}: the unit "
                 r"is in a crate that passed \texttt{cargo check}, tests, and Clippy.", "tab:v2-cascade",
                 ["Library", "Units", "Candidate", "Generated", "Crate", "Policy", "Accepted"],
                 body, "lrrrrrr")


def _failures(row: dict) -> dict:
    value = row.get("failure_categories") or {}
    return json.loads(value) if isinstance(value, str) else value


def baseline_table(rows: dict) -> str:
    modes = ("safemap_guided", "llm_only", "llm_plain", "safemap_deterministic", "c2rust_only")
    body, total = [], Counter()
    for name in ORIG + EXT:
        if (name, "safemap_guided") not in rows:
            continue
        units = n(rows.get((name, "safemap_guided")), "total_units")
        vals = [n(rows.get((name, m)), ACCEPTED) for m in modes]
        c2r = rows.get((name, "c2rust_only")) or {}
        if str(c2r.get("c2rust_compile")) != "True":
            vals[-1] = f"{vals[-1]}$^\\dagger$"
        calls = [n(rows.get((name, m)), "llm_calls") for m in modes[:2]]
        total.update({"u": units, **{m: v for m, v in zip(modes[:4], vals)},
                      "cg": calls[0], "cl": calls[1]})
        body.append([name, units, *vals, f"{calls[0]} / {calls[1]}"])
        if name == ORIG[-1]:
            body.append("---")
    body += ["---", ["Total", total["u"], *(total[m] for m in modes[:4]), 0,
                     f"{total['cg']} / {total['cl']}"]]
    return table("Accepted units per configuration on the held-out libraries (first run). "
                 "One-shot: given the planned signatures; plain: C sources only (amendment 2). "
                 "LLM calls: guided / one-shot. $^\\dagger$C2Rust output did not compile.",
                 "tab:v2-baselines",
                 ["Library", "Units", "Guided", "One-shot", "Plain", "Rules", "C2Rust", "LLM calls"],
                 body, "lrrrrrrr")


def refusal_table(rows: dict) -> str:
    counts = Counter()
    for name in ORIG + EXT:
        r = rows.get((name, "safemap_guided"))
        if r:
            counts.update(_failures(r))
    labels = {
        "requires_manual_refactor": "Manual refactor (global state, I/O, allocation protocols)",
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
                 r"libraries (first run).",
                 "tab:v2-refusals", ["Reason", "Functions"], body, "lr")


def repeat_table(runs: list[tuple[str, dict]]) -> str:
    body = []
    for label, rows in runs:
        g = sum(n(rows.get((x, "safemap_guided")), ACCEPTED) for x in ORIG + EXT)
        o = sum(n(rows.get((x, "llm_only")), ACCEPTED) for x in ORIG + EXT)
        plain = sum(n(rows.get((x, "llm_plain")), ACCEPTED) for x in ORIG + EXT)
        libs = sum(1 for x in ORIG + EXT if (x, "safemap_guided") in rows)
        body.append([label, libs, g, o, plain])
    return table("Accepted units across repeated LLM runs (identical inputs and configuration). "
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
    outputs = {
        "corpus.tex": corpus_table(first),
        "cascade.tex": cascade_table(first),
        "baselines.tex": baseline_table(first),
        "refusals.tex": refusal_table(first),
        "repeats.tex": repeat_table(repeats),
        "ablations.tex": ablation_table(ablation),
        "development.tex": development_table(dev),
    }
    for name, text in outputs.items():
        (out / name).write_text("% Generated by scripts/generate_v2_manuscript_tables.py; do not edit.\n"
                                + text, encoding="utf-8")
    print("wrote", ", ".join(outputs))


if __name__ == "__main__":
    main()

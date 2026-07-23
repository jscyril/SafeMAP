# SafeMAP Artifact Reproduction

Use this entry point to regenerate the paper-facing CSVs, Markdown summaries,
Markdown and LaTeX paper tables, combined evaluation summary, and tool-version
metadata:

```bash
make paper-artifacts
```

Equivalent direct command:

```bash
python scripts/reproduce_paper_artifacts.py
```

Before a long benchmark run, validate local tools, selected modes, LLM key
status, and output reuse with:

```bash
python -m safemap.cli final-eval \
  --benchmarks examples \
  --output reports/final \
  --mode safemap_full \
  --dry-run
```

By default, each invocation uses a fresh timestamped working directory under
`reports/.reproduction/` and publishes only the canonical paper-facing files to
`reports/publication/`. This prevents preserved `.safemap/runs/` directories or
temporary differential harnesses from leaking into the publication snapshot.

The script runs:

- SafeMAP microbenchmarks: `examples` in `safemap_full` mode.
- Case studies: `case_studies` in `safemap_full` mode.
- C2Rust strict-policy baseline: `examples` in `c2rust_only` mode.
- Combined summary in the fresh working directory.
- Tool metadata in the fresh working directory.
- A clean snapshot under `reports/publication/`, including the command
  manifest and all CSV, Markdown, and LaTeX table artifacts. The manifest
  records whether the Git worktree was dirty and includes a SHA-256 checksum
  for every published file.

To choose explicit locations, use:

```bash
python scripts/reproduce_paper_artifacts.py \
  --reports-dir /tmp/safemap-paper-run \
  --snapshot-dir reports/publication
```

The working directory must be empty. The script fails before launching the
evaluation if reusing it could mix old and new results.

After regeneration, print concise paper-facing metric sentences with:

```bash
python -m safemap.cli metric-summary
```

The benchmark CSVs expose separate Cargo check, Cargo test, Clippy, Miri, and
differential-testing statuses. The generated Markdown and LaTeX paper tables
also include validation-status summaries so skipped, unsupported, failed, and
not-applicable checks are visible instead of folded into one failure bucket.
Schema `safemap.benchmark_results.v2` additionally includes C LOC, function and
parameter counts, pointer-parameter density, approximate cyclomatic complexity,
and unsupported-construct counts for dataset characterization.

The current locally generated C2Rust baseline reports `0 / 72` accepted units because
two baseline rows did not produce complete metrics. The default reproduction
script passes `--allow-denominator-mismatch` to make that discrepancy explicit
in the workflow. Use `make paper-artifacts-strict` to fail instead when the
C2Rust denominator differs from the SafeMAP microbenchmark denominator.

Optional LLM subset results are excluded by default. Include a specific result
set explicitly with `--llm-csv reports/gemini_benchmark_results.csv`; the exact
CSV will then be copied into the clean snapshot. LLM runs require an API key and
fixed provider/model settings, and remain diagnostic evidence unless the paper
clearly labels the bounded subset.

Expected external tools:

- Python 3.11 or newer.
- Rust toolchain with Cargo and Clippy.
- Clang/libclang.
- C2Rust for the baseline lane.
- Miri is optional and currently disabled by default.

Runtime depends on installed external tools and validation settings. Generated
working directories under `reports/.reproduction/` are ignored by Git. The
clean `reports/publication/` snapshot is intentionally trackable and contains
no `.safemap` run history or build output.

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

The script runs:

- SafeMAP microbenchmarks: `examples` in `safemap_full` mode.
- Case studies: `case_studies` in `safemap_full` mode.
- C2Rust strict-policy baseline: `examples` in `c2rust_only` mode.
- Combined summary: `reports/combined_evaluation.md`.
- Tool metadata: `reports/artifact_metadata.json`.
- Command manifest: `reports/reproduction_manifest.json`.

After regeneration, print concise paper-facing metric sentences with:

```bash
python -m safemap.cli metric-summary
```

The benchmark CSVs expose separate Cargo check, Cargo test, Clippy, Miri, and
differential-testing statuses. The generated Markdown and LaTeX paper tables
also include validation-status summaries so skipped, unsupported, failed, and
not-applicable checks are visible instead of folded into one failure bucket.

The current checked-in C2Rust baseline reports `0 / 72` accepted units because
two baseline rows did not produce complete metrics. The default reproduction
script passes `--allow-denominator-mismatch` to make that discrepancy explicit
in the workflow. Use `make paper-artifacts-strict` to fail instead when the
C2Rust denominator differs from the SafeMAP microbenchmark denominator.

Optional LLM subset results are included only when
`reports/gemini_benchmark_results.csv` exists. LLM runs require an API key and
fixed provider/model settings; they are diagnostic evidence unless the paper
clearly labels the bounded subset.

Expected external tools:

- Python 3.11 or newer.
- Rust toolchain with Cargo and Clippy.
- Clang/libclang.
- C2Rust for the baseline lane.
- Miri is optional and currently disabled by default.

Runtime depends on installed external tools and validation settings. Generated
run directories under `reports/*/.safemap/` are ignored by Git; paper-facing
CSV/Markdown/manifest snapshots can be regenerated with the commands above.
Use a fresh output directory for publication snapshots when possible, because
SafeMAP preserves previous `.safemap/runs/` directories for audit history.

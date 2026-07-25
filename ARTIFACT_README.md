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

Before a long benchmark run, validate local tools, selected modes, and output
reuse with:

```bash
python -m safemap.cli final-eval \
  --benchmarks examples \
  --output reports/final \
  --mode safemap_deterministic \
  --dry-run
```

By default, each invocation uses a fresh timestamped working directory under
`reports/.reproduction/` and publishes only the canonical paper-facing files to
`reports/publication/`. This prevents preserved `.safemap/runs/` directories or
temporary differential harnesses from leaking into the publication snapshot.

The script runs:

- SafeMAP microbenchmarks: `examples` in `safemap_deterministic` mode.
- Case studies: `case_studies` in `safemap_deterministic` mode.
- Pinned LLVM corpus: `external_corpus/llvm_test_suite_misc/projects` in
  `safemap_deterministic` mode, including reference-output validation.
- C2Rust strict-policy baseline: `examples` in `c2rust_only` mode.
- Static-guidance ablation: `examples` in `safemap_no_static_guidance` mode.
- Combined summary in the fresh working directory.
- Tool metadata in the fresh working directory.
- A clean snapshot under `reports/publication/`, including the command
  manifest and all CSV, Markdown, and LaTeX table artifacts. The manifest
  records whether the Git worktree was dirty and includes a SHA-256 checksum
  for every published file.

The independently authored LLVM external corpus can also be reproduced
separately:

```bash
make external-corpus-artifacts
```

That command uses a fresh timestamped work directory, evaluates the ten pinned
programs under
`external_corpus/llvm_test_suite_misc/projects` in
`safemap_deterministic` mode and writes CSV, Markdown, LaTeX, and manifest
artifacts under `reports/external-corpus/`. It does not require C2Rust or an LLM
provider. Corpus inputs, upstream reference outputs, source hashes, the
reviewed contextual harness, the selection rule, and licenses are tracked in
the repository. The canonical paper reproduction includes the same external
evaluation under `reports/publication/external-corpus/`.

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

The current C2Rust baseline reports `0 / 76` accepted units under the same
eligible-unit denominator as deterministic SafeMAP. Reproduction rejects
denominator mismatches by default; `--allow-denominator-mismatch` exists only
for explicitly documented exceptional runs.

LLM experiments are excluded from the paper reproduction workflow and
publication snapshot.

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

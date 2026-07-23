# SafeMAP

SafeMAP is a safe-first research prototype for analysis-guided C-to-Rust
migration.

It attempts to translate statically eligible C functions or small modules into
fully safe, idiomatic Rust. C2Rust is used as a baseline/reference lane, not as
the main successful output. A SafeMAP translation is counted as fully safe only
when the final Rust compiles with `#![forbid(unsafe_code)]`, exposes no
raw-pointer public API, and passes available validation.

This is a research prototype, not a production compiler.

## Research Goal

SafeMAP is designed to support the claim that a safe-first migration pipeline can
produce fully safe Rust for a restricted, statically identifiable subset of C
programs while clearly reporting unsupported or unsafe-required code.

The main success metric is:

```text
fully_safe_translation_unit_acceptance_rate
```

Unsafe reduction is reported, but unsafe reduction alone is not treated as
successful safe migration.

## Pipeline

```text
C input
  -> ingestion and build recovery
  -> C static analysis
  -> safety eligibility classification
  -> C idiom detection
  -> migration planning
  -> safe Rust synthesis or LLM-guided rewrite
  -> compiler-guided repair under forbid(unsafe_code)
  -> validation
  -> metrics and research reports
```

C2Rust runs separately:

```text
C input
  -> C2Rust baseline
  -> unsafe/raw-pointer metrics
  -> baseline compile status
  -> comparison against SafeMAP final output
```

## Current MVP Scope

Supported MVP idioms include:

- simple scalar integer functions
- integer boolean idioms to `bool`
- pointer-length arrays to `&[T]` or `&mut [T]`
- output parameters to return values
- multiple output parameters to tuple returns
- return-code plus output-parameter to `Result<T, i32>`
- nullable pointers to `Option<&T>` or `Option<&mut T>`
- mutable scalar pointer updates to `&mut T`
- simple C string input to `&str`
- simple local allocation buffers to `Vec<T>`
- single owned allocation to `Box<T>`
- broader allocation idioms in analysis/planning and reporting

Unsupported or manual-review constructs include:

- complex macros
- unions
- function pointers
- inline assembly
- volatile memory access
- pointer-integer casts
- unresolved aliasing
- custom allocators
- large multi-file build-system migration

## Current Artifact Status

As of the current local validation pass:

| Area | Current status |
|---|---|
| Test suite | `111 passed` |
| MVP benchmark examples | `40` example projects under `examples/` |
| SafeMAP-only final eval | `37 / 76` eligible units accepted |
| Supported examples with differential pass | `36` |
| Case-study modules | `5` authored modules, `15 / 20` eligible units accepted |
| External corpus | `10` pinned LLVM test-suite programs, `1 / 22` eligible units accepted by deterministic synthesis |
| C2Rust-only baseline | `0 / 72` fully safe accepted units in the canonical publication snapshot because two baseline rows did not produce complete metrics |
| LLM smoke test | Ollama `llm_only` on `simple_sum` compiled and differential-passed; full LLM baseline remains latency/model dependent |
| Accepted final Rust policy | `#![forbid(unsafe_code)]`, no unsafe blocks/functions, no raw-pointer public API |
| Benchmark table export | `benchmark_results.csv`, `benchmark_results.md`, `paper_tables.md`, `paper_tables.tex`, `manifest.json`, plus combined evaluation summary |

The most recent SafeMAP-only final evaluation was verified locally with:

```bash
python -m safemap.cli final-eval \
  --benchmarks examples \
  --output /tmp/safemap-final-eval-40-benchmarks \
  --mode safemap_full
```

Observed result:

```text
rows: 40
safemap_full accepted units: 37 / 76
```

The intentionally unsupported benchmark examples are still reported separately
and should not be interpreted as SafeMAP translation failures for supported
idioms.

Case-study modules are evaluated separately with:

```bash
python -m safemap.cli final-eval \
  --benchmarks case_studies \
  --output /tmp/safemap-case-studies \
  --mode safemap_full
```

Observed case-study result:

```text
rows: 5
safemap_full accepted units: 15 / 20
all 5 case-study modules passed differential testing
```

The independently authored external corpus is pinned and selected without using
SafeMAP outcomes. It is evaluated separately so authored and external-validity
evidence are not mixed:

```bash
make external-corpus-artifacts
```

Observed deterministic result:

```text
rows: 10
accepted units: 1 / 22
C LOC: 589
analyzed functions: 32
```

The low external acceptance rate is retained as a result, not filtered out.
See `external_corpus/README.md` for the upstream commit, licensing, exact
selection rule, checksums, exclusions, and current validation limitations.

After generating the benchmark, case-study, C2Rust baseline, and LLM subset CSVs,
combine paper-facing results with:

```bash
python -m safemap.cli combined-eval \
  --output reports/publication/combined_evaluation.md \
  --main-csv reports/publication/final/benchmark_results.csv \
  --case-study-csv reports/publication/case-studies/benchmark_results.csv \
  --c2rust-csv reports/publication/c2rust-only/benchmark_results.csv \
  --allow-denominator-mismatch
```

The explicit denominator override is required for the current canonical C2Rust
snapshot because it reports `0 / 72` accepted units while the SafeMAP
microbenchmark CSV reports `37 / 76`.

## Repository Layout

```text
safemap/                         Python package
  analysis/                      C/Rust analysis and eligibility classification
  ingestion/                     file discovery and compile database recovery
  translation/                   planning, C2Rust baseline, safe synthesis, rewrite
  repair/                        compiler-guided repair support
  validation/                    cargo, clippy, miri, differential validation
  metrics/                       unsafe/raw-pointer metrics and reports
external_corpus/                 pinned independently authored evaluation inputs
examples/                        small C migration examples
tests/                           pytest suite
reports/sample_report.md         illustrative report sample
safemap.example.yaml             example configuration
safemap.gemini.yaml              Google AI Studio / Gemini API config
safemap.ollama.yaml              local Ollama OpenAI-compatible config
SAFEMAP_CODEX_SOURCE_OF_TRUTH.md project design source of truth
SAFEMAP_RESEARCH_TODO.md         research status and next steps
CONTRIBUTING.md                  validation and contribution checklist
docs-site/                       static GitHub Pages documentation
```

## Installation

Use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,rust-analysis]"
```

Verify:

```bash
python -m safemap.cli --help
pytest
```

## External Tools

Recommended tools:

- Rust toolchain with Cargo and Clippy
- Clang and libclang
- C2Rust for baseline comparison
- Bear for Make projects without `compile_commands.json`
- Miri for optional undefined-behavior checks

Missing optional tools are recorded as skipped, unsupported, or failed with a
reason. They should not be silently treated as successful results.

### C2Rust Notes

C2Rust can be sensitive to LLVM and system-header versions. This repository has
support for LLVM 14 style local installs through environment overrides:

```bash
export SAFEMAP_C2RUST_CLANG=/opt/llvm-14.0.6/bin/clang
export SAFEMAP_C2RUST_RESOURCE_DIR=/opt/llvm-14.0.6/lib/clang/14.0.6
export SAFEMAP_C2RUST_LIB_DIR=/opt/llvm-14.0.6/lib
```

The C2Rust baseline is evaluated separately. It is not counted as a SafeMAP
success unless it independently satisfies the fully safe acceptance criteria.

## Configuration

Start from:

```bash
cp safemap.example.yaml safemap.local.yaml
```

Do not put real API keys in YAML files committed to Git. API keys are read from
environment variables.

For OpenAI-compatible providers:

```bash
export OPENAI_API_KEY="your_key"
```

For Gemini through the Gemini OpenAI-compatible API:

```bash
export GEMINI_API_KEY="your_key"
```

and use the included Google AI Studio/Gemini config:

```bash
python -m safemap.cli benchmark \
  --benchmarks examples \
  --output reports/gemini_benchmark_results.csv \
  --config safemap.gemini.yaml
```

The relevant configuration is:

```yaml
llm:
  provider: openai_compatible
  model: gemini-3.5-flash
  base_url: https://generativelanguage.googleapis.com/v1beta/openai/
  temperature: 0.1
  max_tokens: 4096
  timeout_seconds: 120
  api_key_env: GEMINI_API_KEY
```

`SAFEMAP_MODEL` and `SAFEMAP_BASE_URL` can override the model and base URL.
Do not commit real API keys; keep them in your shell environment or local
secret manager.

For local Ollama models such as Gemma:

```bash
export OLLAMA_API_KEY=dummy
python -m safemap.cli benchmark \
  --benchmarks examples \
  --output reports/ollama_gemma4_12b_benchmark_results.csv \
  --config safemap.ollama.yaml \
  --mode llm_only
```

The included Ollama config expects the model tag `gemma4:12b` and base URL
`http://localhost:11434/v1`.

## Usage

Run the full pipeline:

```bash
python -m safemap.cli run \
  --input examples/output_parameter \
  --output results \
  --config safemap.example.yaml
```

After a run, inspect:

```bash
find results/.safemap/runs -maxdepth 1 -type d | sort
cat results/.safemap/runs/<run-id>/reports/report.md
cat results/.safemap/runs/<run-id>/reports/metrics.json
```

Run individual stages:

```bash
python -m safemap.cli ingest --input examples/output_parameter --output work
python -m safemap.cli analyze-c --workdir work
python -m safemap.cli translate-baseline --workdir work
python -m safemap.cli analyze-rust --workdir work
python -m safemap.cli plan --workdir work
python -m safemap.cli rewrite --workdir work --config safemap.example.yaml
python -m safemap.cli repair --workdir work --config safemap.example.yaml
python -m safemap.cli validate --workdir work --config safemap.example.yaml
python -m safemap.cli report --workdir work
```

Run benchmark modes:

```bash
python -m safemap.cli benchmark \
  --benchmarks examples \
  --output reports/benchmark_results.csv \
  --config safemap.example.yaml
```

Check benchmark inputs, selected modes, external tools, LLM key status, and
whether an output directory already contains prior run artifacts without running
the benchmark:

```bash
python -m safemap.cli benchmark \
  --benchmarks examples \
  --output reports/benchmark_results.csv \
  --mode safemap_full \
  --dry-run
```

Export paper-ready Markdown tables from a benchmark CSV:

```bash
python -m safemap.cli export-tables \
  --input reports/benchmark_results.csv \
  --output reports/paper_tables.md
```

Run a durable final evaluation bundle:

```bash
python -m safemap.cli final-eval \
  --benchmarks examples \
  --output reports/final \
  --mode safemap_full
```

Run only the C2Rust strict-policy baseline:

```bash
python -m safemap.cli final-eval \
  --benchmarks examples \
  --output reports/c2rust-only \
  --mode c2rust_only
```

Run only the bounded LLM subset with an OpenAI-compatible config:

```bash
python -m safemap.cli benchmark \
  --benchmarks examples \
  --output reports/gemini_benchmark_results.csv \
  --config safemap.gemini.yaml \
  --mode llm_only
```

Inspect saved runs:

```bash
python -m safemap.cli latest-run --output reports/final
python -m safemap.cli summarize-runs --output reports/final
```

Print a publication-ready metric summary from canonical CSV inputs:

```bash
python -m safemap.cli metric-summary \
  --main-csv reports/publication/final/benchmark_results.csv \
  --case-study-csv reports/publication/case-studies/benchmark_results.csv \
  --c2rust-csv reports/publication/c2rust-only/benchmark_results.csv
```

Benchmark modes:

- `c2rust_only`: run C2Rust only and apply SafeMAP's strict final-output policy
  as a baseline.
- `llm_only`: ask the configured OpenAI-compatible LLM for direct safe Rust
  output without C2Rust or static guidance.
- `c2rust_llm_unguided`: run C2Rust, then ask the LLM to rewrite without
  SafeMAP static guidance.
- `safemap_deterministic`: use static guidance and deterministic synthesis
  without C2Rust or an LLM; this is the reproducible external-corpus lane.
- `safemap_full`: run the full analysis-guided SafeMAP pipeline.

For publication snapshots, use `make paper-artifacts`. It evaluates in a fresh
timestamped work directory and publishes only the canonical allowlisted files.

## Output Artifacts

Runs are written under:

```text
<output>/.safemap/runs/<timestamp>-<project>-<id>/
```

Important artifacts:

- `project.json`
- `analysis/c_analysis.json`
- `analysis/translation_units.json`
- `analysis/eligibility.json`
- `plans/*.json`
- `baseline/rust/`
- `baseline/compile.json`
- `final/rust/`
- `validation/results.json`
- `reports/report.md`
- `reports/metrics.json`
- `reports/comparison.csv`
- `logs/c2rust.json`

Benchmark CSVs include per-check validation status fields for Cargo check,
Cargo test, Clippy, Miri, and differential testing, plus
`validation_status_counts` so skipped, unsupported, failed, and not-applicable
outcomes can be reported separately. Result schema
`safemap.benchmark_results.v2` also records per-project C LOC, analyzed function
and parameter counts, pointer-parameter density, total and average approximate
cyclomatic complexity, and unsupported-construct counts. Pointer density is
defined as pointer parameters divided by all analyzed function parameters.

Generated run outputs are ignored by Git.

## Development

Run:

```bash
pytest
python -m compileall -q safemap
```

Current expected test result:

```text
111 passed
```

## Reproducing Paper Artifacts

Regenerate the paper-facing report bundle with:

```bash
make paper-artifacts
```

This runs the SafeMAP microbenchmarks, case studies, C2Rust baseline, combined
summary, and tool-version capture in a fresh ignored workspace. It publishes:

- `reports/publication/final/`
- `reports/publication/case-studies/`
- `reports/publication/c2rust-only/`
- `reports/publication/combined_evaluation.md`
- `reports/publication/artifact_metadata.json`
- `reports/publication/reproduction_manifest.json`

The reproduction manifest records exact commands, tool versions, dirty-tree
state, and SHA-256 checksums for every published file.

Use `make paper-artifacts-strict` to fail when the C2Rust denominator differs
from the SafeMAP microbenchmark denominator. See `ARTIFACT_README.md` for the
artifact policy and expected external tools.

## Git Hygiene

Do not commit:

- real API keys
- `.env` files
- virtual environments
- generated SafeMAP run directories
- Cargo `target/` directories
- Python caches
- local editor or agent state

Use `.env.example` for placeholder environment variables only.

## GitHub Readiness Checklist

Before pushing:

- Run `pytest -q`.
- Run `python -m compileall -q safemap tests`.
- Ensure `.env` is not staged.
- Keep generated run directories out of Git.
- Commit benchmark source examples and expected metadata.
- Commit documentation updates in `README.md`, `SAFEMAP_RESEARCH_TODO.md`, and
  `docs-site/`.
- Review `CONTRIBUTING.md` for validation and artifact policy.
- Commit config templates such as `safemap.gemini.yaml`, `safemap.ollama.yaml`,
  and `.env.example`, but never real keys.

Optional release artifact generation:

```bash
python -m safemap.cli final-eval \
  --benchmarks examples \
  --output reports/final \
  --mode safemap_full
```

Generated `reports/final/` artifacts are useful for local review. Commit only
the clean `reports/publication/` snapshot; do not hand-edit reported metrics.

## Known Limitations

- SafeMAP is not a full C compiler or production migration tool.
- Deterministic safe synthesis is intentionally narrow.
- LLM rewrite/repair depends on configured external model access.
- C2Rust may require old LLVM runtime libraries and may emit Rust that fails on
  stable Rust due to obsolete feature gates.
- Differential testing is limited and not a formal equivalence proof.
- Unsupported units are rejected or reported instead of forced through unsafe
  migration.

## Research Notes

For paper planning, see:

```text
SAFEMAP_RESEARCH_TODO.md
```

Use the generated metrics and reports directly. Do not invent benchmark results.

## Documentation Site

A static book-style documentation site lives in:

```text
docs-site/
```

It can be opened locally with `docs-site/index.html` or deployed to GitHub Pages
using the included `.github/workflows/pages.yml` workflow. In GitHub repository
settings, set Pages source to **GitHub Actions**.

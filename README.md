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

- pointer-length arrays to `&[T]` or `&mut [T]`
- output parameters to return values
- return-code plus output-parameter to `Result<T, i32>`
- nullable pointers to `Option<&T>` or `Option<&mut T>`
- simple allocation idioms in analysis/planning

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

## Repository Layout

```text
safemap/                         Python package
  analysis/                      C/Rust analysis and eligibility classification
  ingestion/                     file discovery and compile database recovery
  translation/                   planning, C2Rust baseline, safe synthesis, rewrite
  repair/                        compiler-guided repair support
  validation/                    cargo, clippy, miri, differential validation
  metrics/                       unsafe/raw-pointer metrics and reports
examples/                        small C migration examples
tests/                           pytest suite
reports/sample_report.md         illustrative report sample
safemap.example.yaml             example configuration
SAFEMAP_CODEX_SOURCE_OF_TRUTH.md project design source of truth
SAFEMAP_RESEARCH_TODO.md         research status and next steps
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

and configure:

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

Benchmark modes:

- `c2rust_only`
- `llm_only`
- `c2rust_llm_unguided`
- `safemap_full`

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

Generated run outputs are ignored by Git.

## Development

Run:

```bash
pytest
python -m compileall -q safemap
```

Current expected test result:

```text
31 passed
```

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

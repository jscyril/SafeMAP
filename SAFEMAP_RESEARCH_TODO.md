# SafeMAP Research TODO and Status

This file summarizes the current SafeMAP prototype state for research-paper planning.

## Completed

### Source-of-Truth Alignment

- Reframed SafeMAP as a safe-first C-to-Rust migration prototype.
- Treats C2Rust as a baseline/reference lane, not as the final SafeMAP success path.
- Distinguishes fully safe accepted Rust from unsafe-reduced, partial, failed, or unsupported output.
- Reports `fully_safe_translation_unit_acceptance_rate` as the main success metric.

### Pipeline and Artifacts

- Keeps timestamped run directories under:

  ```text
  results/.safemap/runs/<timestamp>-<project>-<id>/
  ```

- Writes key artifacts:
  - `project.json`
  - `analysis/c_analysis.json`
  - `analysis/translation_units.json`
  - `analysis/eligibility.json`
  - `plans/*.json`
  - `baseline/rust/`
  - `final/rust/`
  - `validation/results.json`
  - `reports/report.md`
  - `reports/metrics.json`
  - `reports/comparison.csv`

### Eligibility Classification

- Added conservative safety eligibility classification.
- Uses required categories:
  - `safe_translatable`
  - `safe_translatable_with_api_change`
  - `requires_safe_wrapper`
  - `requires_manual_refactor`
  - `unsafe_required`
  - `unsupported`
- Detects and rejects unsupported or risky constructs such as:
  - unions
  - function pointers
  - inline assembly
  - volatile access
  - unresolved pointer ownership
  - unresolved aliasing risk

### C Idiom Support

- Supports MVP analysis/planning for:
  - simple scalar functions
  - pointer-length arrays to Rust slices
  - mutable pointer-length buffers to mutable Rust slices
  - output parameters to return values
  - multiple output parameters to tuple returns
  - mutable scalar pointers to `&mut T`
  - return-code plus output-parameter to `Result<T, i32>`
  - nullable pointers to `Option<&T>`
  - simple C string inputs to Rust `&str`
  - integer boolean idioms to Rust `bool`
  - simple allocation idioms in analysis/planning

### Safe Rust Generation

- Added deterministic safe synthesis for clear MVP examples.
- Generated final Rust includes:

  ```rust
  #![forbid(unsafe_code)]
  ```

- Current safe synthesis covers examples such as:
  - `simple_sum`
  - `boolean_int`
  - `pointer_length_array`
  - `mutable_buffer`
  - `multiple_outputs`
  - `simple_pointer`
  - `string_length`
  - `output_parameter`
  - `nullable_pointer`
  - `error_code`
  - `malloc_free`

### LLM Integration

- Existing LLM abstraction is preserved.
- OpenAI-compatible client supports providers such as OpenAI and Gemini OpenAI-compatible API.
- LLM errors now include provider/model/base URL context and actionable
  diagnostics for missing keys, authentication failures, and quota/rate limits.
- Prompts now explicitly forbid:
  - `unsafe`
  - `unsafe fn`
  - `unsafe impl`
  - `extern "C"`
  - `*const`
  - `*mut`
  - placeholder code such as `todo!()` and `unimplemented!()`
- LLM responses are rejected if they introduce forbidden unsafe constructs.

### C2Rust Baseline

- C2Rust installation verified with `c2rust 0.22.1`.
- SafeMAP now generates compile databases for single-file example directories.
- SafeMAP can pass LLVM 14 library/include paths to C2Rust subprocesses.
- Added minimal C2Rust-only header shims for common headers:
  - `stdio.h`
  - `stdlib.h`
  - `string.h`
- C2Rust baseline artifacts are generated separately from SafeMAP final output.

### Validation and Metrics

- Runs validation with:
  - `cargo check`
  - `cargo test`
  - `cargo clippy`
  - optional Miri
  - differential testing when applicable
- Differential testing now compares executable-compatible examples and known MVP
  library translations through generated Rust harness binaries.
- Function-level differential harnesses generate deterministic randomized test
  cases for supported signatures using `validation.differential_test_inputs`.
- Differential testing still records `not_applicable` when no comparable harness
  is available.
- Reports:
  - eligible units
  - fully safe accepted units
  - unsafe blocks/functions
  - raw pointer counts
  - raw-pointer public API counts
  - idiom migration counts
  - failure categories
- Fully safe accepted units are counted only when the planned function is present in the final Rust output.

### Tests

- Test suite currently passes:

  ```text
  82 passed
  ```

- Added tests for:
  - eligibility classification
  - migration plan schema fields
  - single-source directory compile DB generation
  - safe synthesis
  - C2Rust compile DB/resource behavior
  - benchmark dataset completeness and expected eligibility/planning metadata
  - final-output presence before fully safe acceptance credit
  - function-level differential harnesses for library-style SafeMAP outputs
  - randomized differential harness generation
  - benchmark status, mode filtering, paper-table export, and aggregate table generation
  - final evaluation artifact generation and run summaries
  - LLM, C2Rust, and Miri diagnostic classification
  - Miri pass/fail count parsing and benchmark export fields

## Current Known Limitations

- SafeMAP is still an MVP research prototype, not a production compiler.
- It does not translate arbitrary C projects.
- Safe synthesis is intentionally narrow and pattern-based.
- C2Rust output may fail to compile on stable Rust because C2Rust emits old nightly feature gates such as:

  ```rust
  #![feature(raw_ref_op)]
  ```

- C2Rust can be sensitive to host LLVM/glibc versions.
- Differential testing is limited and mostly works for executable-compatible examples.
- Multi-file project migration is not yet robust.
- Complex macros, unions, function pointers, custom allocators, volatile memory, inline assembly, and pointer-integer casts are rejected or reported.
- LLM rewrite/repair requires an API key and has not yet been evaluated over a large benchmark set.

## Paper-Critical Work Left

### P0: Benchmark Dataset

- Status: completed for the MVP paper dataset.
- Benchmark examples under `examples/` now include:
  - `simple_sum`
  - `simple_subtract`
  - `simple_multiply`
  - `simple_divide`
  - `simple_modulo`
  - `boolean_int`
  - `boolean_negative`
  - `boolean_nonzero`
  - `boolean_greater_equal`
  - `boolean_less_equal`
  - `pointer_length_array`
  - `array_max`
  - `array_total`
  - `mutable_buffer`
  - `mutable_buffer_decrement`
  - `mutable_buffer_add_two`
  - `mutable_buffer_subtract_two`
  - `multiple_outputs`
  - `min_max_outputs`
  - `sum_diff_outputs`
  - `output_square`
  - `output_double`
  - `simple_pointer`
  - `simple_pointer_decrement`
  - `simple_pointer_double`
  - `string_length`
  - `string_length_size_t`
  - `string_length_long`
  - `output_parameter`
  - `nullable_pointer`
  - `nullable_pointer_zero`
  - `error_code`
  - `error_code_product`
  - `malloc_free`
  - `malloc_free_constant`
  - `malloc_vec`
  - `unsupported_union`
  - `unsupported_function_pointer`
  - `unsupported_volatile`
  - `unsupported_inline_asm`
- Each benchmark includes:
  - C source
  - expected eligibility category
  - expected migration plan
  - expected safe Rust behavior where applicable

### P1: Evaluation Runs

- Status: partially complete.
- Current SafeMAP-only evaluation run covered all benchmark examples and wrote:

  ```text
  /tmp/safemap-full-expanded.csv
  /tmp/safemap-full-expanded.md
  /tmp/safemap-paper-tables.md
  /tmp/safemap-final-eval/
  ```

- Observed SafeMAP-only summary:
  - 40 benchmark rows
  - `safemap_full`: 37 accepted units out of 76 eligible units
  - 36 supported MVP examples pass differential testing
  - unsupported examples are rejected or reported separately
- Remaining final-paper evaluation work:
  - `c2rust_only`
  - `llm_only`
  - `c2rust_llm_unguided`
- Re-run LLM-dependent modes with a configured model/API key.
- Do not hand-edit reported metrics.

### P2: Differential Testing

- Status: completed for current MVP supported examples.
- Added differential harnesses for:
  - integer functions
  - boolean integer returns
  - integer arrays/slices
  - output parameters
  - nullable pointers
  - mutable integer buffers
  - mutable scalar pointer updates
  - multiple output parameters returned as tuples
  - simple C string inputs translated to `&str`
  - simple allocation/`Box<T>` examples
  - simple allocation-buffer/`Vec<T>` examples
- Remaining:
  - multi-function/project-level harnesses beyond the MVP examples

### P3: LLM Evaluation

- Status: ready for API-backed run.
- Added `safemap.gemini.yaml` for Google AI Studio / Gemini OpenAI-compatible
  API usage with:
  - `api_key_env: GEMINI_API_KEY`
  - `base_url: https://generativelanguage.googleapis.com/v1beta/openai/`
  - `model: gemini-3.5-flash`
- Direct LLM translation now records:
  - LLM call count
  - input tokens
  - output tokens
- Direct LLM translation now rejects forbidden unsafe/raw-pointer/placeholder
  constructs before writing a final crate.
- Offline static-client LLM benchmark smoke passed for `simple_sum`:
  - `llm_only`: compile passed, differential passed
  - `c2rust_llm_unguided`: compile passed, differential passed
- Remaining:
  - export `GEMINI_API_KEY`
  - run Google AI Studio-backed benchmark:

    ```bash
    python -m safemap.cli benchmark \
      --benchmarks examples \
      --output reports/gemini_benchmark_results.csv \
      --config safemap.gemini.yaml
    ```

- Run LLM rewrite/repair on examples that deterministic synthesis does not cover.
- Record:
  - prompt artifacts
  - response artifacts
  - rewrite success/failure
  - repair attempts
  - unsafe rejection events
  - compile/test/differential status

### P4: Report Tables

- Status: partially complete.
- Benchmark runner now produces a richer CSV and Markdown summary containing:
  - benchmark summary
  - eligibility classification counts
  - success-by-idiom aggregate table
  - paper-ready table export from saved benchmark CSVs
  - accepted/eligible unit counts
  - fully safe acceptance rate
  - C2Rust baseline comparison
  - LLM-only comparison
  - C2Rust plus LLM unguided comparison
  - SafeMAP full comparison
  - unsafe/raw-pointer reduction
  - failure category distribution
  - validation results
  - durable final-evaluation manifest under `reports/final/`
- Remaining:
  - include real LLM mode results after API-backed evaluation

### P5: Threats to Validity

- Document limitations clearly:
  - benchmark size
  - hand-curated examples
  - dependence on LLVM/C2Rust versions
  - LLM nondeterminism
  - limited differential testing
  - incomplete C language coverage
  - pattern-based deterministic synthesis

## Useful Additions

### Better Safe Synthesis

- Add more deterministic translation patterns:
  - mutable buffer normalization
  - additional allocation and initialization shapes beyond the current `Vec<T>` and `Box<T>` cases
  - simple string parsing to `Result`

### Stronger Analysis

- Improve pointer role classification.
- Add more aliasing evidence.
- Add macro and preprocessor reporting.
- Improve call graph and dependency graph summaries.
- Track external calls more precisely.

### Validation Improvements

- Generate Rust unit tests from C examples.
- Add project-specific validation failure summaries in reports and CLI output.

### C2Rust Baseline Cleanup

- Optionally patch C2Rust baseline artifacts only for compile measurement.
- Record both raw C2Rust output and minimally compile-fixed baseline output separately.
- Do not count compile-fixed C2Rust as SafeMAP success unless it satisfies fully safe acceptance.

### CLI and UX

- Add clearer diagnostics for project-specific validation failures.

## Suggested Immediate Next Steps

1. Configure Gemini with:

   ```bash
   export GEMINI_API_KEY="your_key"
   ```

   and in config:

   ```yaml
   llm:
     provider: openai_compatible
     model: gemini-3.5-flash
     base_url: https://generativelanguage.googleapis.com/v1beta/openai/
     api_key_env: GEMINI_API_KEY
   ```

2. Run a durable SafeMAP-only final-evaluation bundle:

   ```bash
   python -m safemap.cli final-eval \
     --benchmarks examples \
     --output reports/final \
     --mode safemap_full
   ```

3. Inspect generated reports and runs:

   ```bash
   cat reports/final/paper_tables.md
   python -m safemap.cli latest-run --output reports/final
   python -m safemap.cli summarize-runs --output reports/final
   ```

4. Re-run LLM-dependent modes after quota/API access is available.

## Paper Claim Supported by Current MVP

The current prototype supports a conservative claim:

> SafeMAP is a safe-first C-to-Rust migration prototype that generates fully safe Rust for a restricted set of statically eligible C functions. It rejects or reports unsupported units, evaluates generated Rust under `#![forbid(unsafe_code)]`, and compares results against a C2Rust baseline using explicit safety and validation metrics.

Avoid claiming:

- full automatic C-to-Rust migration;
- support for arbitrary C projects;
- formal behavioral equivalence;
- production compiler completeness;
- success based only on unsafe-code reduction.

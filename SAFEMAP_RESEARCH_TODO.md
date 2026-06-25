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
  - pointer-length arrays to Rust slices
  - output parameters to return values
  - return-code plus output-parameter to `Result<T, i32>`
  - nullable pointers to `Option<&T>`
  - simple allocation idioms in analysis/planning

### Safe Rust Generation

- Added deterministic safe synthesis for clear MVP examples.
- Generated final Rust includes:

  ```rust
  #![forbid(unsafe_code)]
  ```

- Current safe synthesis covers examples such as:
  - `pointer_length_array`
  - `output_parameter`
  - `nullable_pointer`
  - `error_code`

### LLM Integration

- Existing LLM abstraction is preserved.
- OpenAI-compatible client supports providers such as OpenAI and Gemini OpenAI-compatible API.
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
- Differential testing now records `not_applicable` for library-only translations.
- Reports:
  - eligible units
  - fully safe accepted units
  - unsafe blocks/functions
  - raw pointer counts
  - raw-pointer public API counts
  - idiom migration counts
  - failure categories

### Tests

- Test suite currently passes:

  ```text
  31 passed
  ```

- Added tests for:
  - eligibility classification
  - migration plan schema fields
  - single-source directory compile DB generation
  - safe synthesis
  - C2Rust compile DB/resource behavior

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

- Add or finalize benchmark examples under `examples/`.
- Minimum recommended examples:
  - `simple_sum`
  - `pointer_length_array`
  - `mutable_buffer`
  - `output_parameter`
  - `nullable_pointer`
  - `error_code_result`
  - `malloc_free`
  - `unsupported_union`
  - `unsupported_function_pointer`
  - `unsupported_volatile`
  - `unsupported_inline_asm`
- Each benchmark should include:
  - C source
  - expected eligibility category
  - expected migration plan
  - expected safe Rust behavior where applicable

### P1: Evaluation Runs

- Run all benchmark modes:
  - `c2rust_only`
  - `llm_only`
  - `c2rust_llm_unguided`
  - `safemap_full`
- Save all run directories.
- Export summary tables for the paper.
- Do not hand-edit reported metrics.

### P2: Differential Testing

- Add differential harnesses for supported function-level examples.
- Prioritize:
  - integer functions
  - integer arrays/slices
  - output parameters
  - nullable pointers
  - simple strings
- Record `not_applicable` only when a comparable harness is not available.

### P3: LLM Evaluation

- Configure Gemini or another OpenAI-compatible model.
- Run LLM rewrite/repair on examples that deterministic synthesis does not cover.
- Record:
  - prompt artifacts
  - response artifacts
  - rewrite success/failure
  - repair attempts
  - unsafe rejection events
  - compile/test/differential status

### P4: Report Tables

- Produce paper-ready tables:
  - benchmark summary
  - eligibility classification counts
  - safe translation success by idiom
  - C2Rust baseline comparison
  - LLM-only comparison
  - C2Rust plus LLM unguided comparison
  - SafeMAP full comparison
  - unsafe/raw-pointer reduction
  - failure category distribution
  - validation results

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
  - multiple output parameters to tuples
  - simple `malloc/free` local buffer to `Vec<T>`
  - single owned allocation to `Box<T>`
  - boolean integer idioms to `bool`
  - simple string parsing to `Result`

### Stronger Analysis

- Improve pointer role classification.
- Add more aliasing evidence.
- Add macro and preprocessor reporting.
- Improve call graph and dependency graph summaries.
- Track external calls more precisely.

### Validation Improvements

- Generate Rust unit tests from C examples.
- Generate C and Rust harnesses for function-level differential tests.
- Add randomized input generation for supported signatures.
- Add optional Miri reporting when installed.

### C2Rust Baseline Cleanup

- Optionally patch C2Rust baseline artifacts only for compile measurement.
- Record both raw C2Rust output and minimally compile-fixed baseline output separately.
- Do not count compile-fixed C2Rust as SafeMAP success unless it satisfies fully safe acceptance.

### CLI and UX

- Add a command to print the latest run directory.
- Add a command to summarize all runs.
- Add a command to export paper tables directly.
- Add clearer diagnostics for missing LLM keys, C2Rust runtime libraries, and LLVM mismatches.

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

2. Run the current examples:

   ```bash
   python -m safemap.cli run --input examples/output_parameter --output results --config safemap.example.yaml
   python -m safemap.cli run --input examples/pointer_length_array --output results --config safemap.example.yaml
   python -m safemap.cli run --input examples/nullable_pointer --output results --config safemap.example.yaml
   python -m safemap.cli run --input examples/error_code --output results --config safemap.example.yaml
   ```

3. Inspect generated reports:

   ```bash
   find results/.safemap/runs -maxdepth 1 -type d | sort
   cat results/.safemap/runs/<run-id>/reports/report.md
   cat results/.safemap/runs/<run-id>/reports/metrics.json
   ```

4. Add unsupported benchmark examples.

5. Run benchmark mode and collect paper tables.

## Paper Claim Supported by Current MVP

The current prototype supports a conservative claim:

> SafeMAP is a safe-first C-to-Rust migration prototype that generates fully safe Rust for a restricted set of statically eligible C functions. It rejects or reports unsupported units, evaluates generated Rust under `#![forbid(unsafe_code)]`, and compares results against a C2Rust baseline using explicit safety and validation metrics.

Avoid claiming:

- full automatic C-to-Rust migration;
- support for arbitrary C projects;
- formal behavioral equivalence;
- production compiler completeness;
- success based only on unsafe-code reduction.

# SafeMAP — Codex Source of Truth

> **Read this file first before making changes.**
>
> This document is the single source of truth for the SafeMAP research prototype. It reconciles the earlier implementation notes with the updated research direction.
>
> **Important correction:** SafeMAP is **not** just “C2Rust + cleanup.” SafeMAP is a **safe-first C-to-Rust migration framework**. C2Rust is still useful, but only as a **baseline, fallback, and semantic/reference artifact**, not as the primary final output.

---

## 1. Project Identity

### Project Name

**SafeMAP: Safe Migration through Analysis-Guided Planning**

### One-Sentence Description

SafeMAP is a research prototype that attempts to translate **statically eligible C functions/modules** into **fully safe, idiomatic Rust**, while using C2Rust only as a baseline/reference and reporting why unsupported C units cannot be safely migrated automatically.

### Research Goal

Given a C file or small C project, SafeMAP should:

1. ingest and analyze the C code;
2. identify functions/modules that are eligible for safe Rust translation;
3. detect common C idioms such as pointer-length arrays, output parameters, nullable pointers, error-code returns, and simple allocation patterns;
4. create a structured migration plan;
5. generate Rust code that is accepted only if it compiles with `#![forbid(unsafe_code)]`;
6. repair compiler errors without introducing unsafe Rust;
7. validate behavior through tests and differential testing where possible;
8. compare against baselines such as C2Rust-only, LLM-only, and unguided C2Rust+LLM;
9. report successful safe translations and explain failures.

### What SafeMAP Is Not

SafeMAP is **not** a production compiler.

SafeMAP is **not** expected to translate arbitrary C projects fully into safe Rust.

SafeMAP is **not** allowed to claim success by merely reducing unsafe code.

SafeMAP must distinguish between:

- **fully safe accepted Rust**, and
- **partially safer / unsafe / unsupported output**.

---

## 2. Core Research Claim

SafeMAP should support this paper claim:

> SafeMAP is a safe-first C-to-Rust migration framework that generates fully safe Rust for statically eligible C translation units. Unlike approaches that mainly reduce unsafe code after C2Rust translation, SafeMAP accepts generated Rust only when it compiles under `#![forbid(unsafe_code)]`, exposes no raw-pointer-based public API, and passes available behavioral validation. Unsupported units are rejected, isolated, or reported with explicit failure reasons.

This framing is strict and academically safer than claiming full automatic migration of all C code.

---

## 3. Definition of “Fully Safe Rust” in SafeMAP

A translated Rust unit is considered **fully safe** only if all of the following are true:

1. The crate/module compiles with:

   ```rust
   #![forbid(unsafe_code)]
   ```

2. The generated Rust contains none of the following:

   - `unsafe { ... }`
   - `unsafe fn`
   - `unsafe impl`
   - `extern "C"` in the translated safe logic
   - raw-pointer-based public APIs such as `*const T` or `*mut T`

3. The generated Rust uses Rust-native abstractions where possible:

   - `&T`
   - `&mut T`
   - `&[T]`
   - `&mut [T]`
   - `Option<T>`
   - `Result<T, E>`
   - tuples
   - `Box<T>`
   - `Vec<T>`
   - Rust enums and structs

4. It passes compilation validation.

5. It passes available unit tests.

6. It passes differential testing where differential testing is applicable.

7. It does not regress into C-style unsafe APIs during compiler repair.

If any of these conditions fail, the unit must not be counted as “fully safe accepted.”

---

## 4. Correct High-Level Pipeline

SafeMAP has two lanes:

### 4.1 Safe-First Main Lane

```text
C file/project
   |
   v
[1] Project ingestion and build recovery
   |
   v
[2] C static analysis
   |
   v
[3] Safety eligibility classification
   |
   v
[4] C idiom detection
   |
   v
[5] Type/API migration planning
   |
   v
[6] LLM-guided safe Rust synthesis
   |
   v
[7] Compiler-guided repair under forbid(unsafe_code)
   |
   v
[8] Validation: cargo check/test, differential tests, Clippy, optional Miri
   |
   v
[9] Metrics and research report
```

### 4.2 C2Rust Baseline/Reference Lane

```text
C file/project
   |
   v
C2Rust baseline
   |
   +--> baseline unsafe/raw-pointer metrics
   +--> baseline compile/test status
   +--> comparison against SafeMAP
   +--> optional structural reference for prompts
   +--> fallback artifact for unsupported units
```

### Critical Rule

The C2Rust output must not be treated as the final successful SafeMAP output unless it also satisfies the strict fully safe acceptance criteria, which it usually will not.

---

## 5. Current Implementation Context

The existing implementation already appears to include:

```text
C project
 -> ingest files/build info
 -> analyze C functions/pointers/idioms
 -> run C2Rust baseline
 -> count Rust unsafe/raw pointers
 -> split into translation units
 -> plan safer Rust APIs
 -> optionally ask an LLM to rewrite functions
 -> optionally repair compiler errors
 -> validate with Cargo/Clippy/Miri/differential tests
 -> generate reports
```

This is close, but it needs to be aligned with the updated source-of-truth framing:

### Required Alignment Changes

1. Make the **safe-first lane** the main result path.
2. Treat C2Rust as a **baseline/reference**, not the final target.
3. Add or strengthen **safety eligibility classification** before rewriting.
4. Add strict safe acceptance using `#![forbid(unsafe_code)]`.
5. Report “fully safe accepted units” separately from “unsafe reduced units.”
6. If LLM rewriting is disabled or fails, do not mark the unit as fully safe.
7. If the final code still contains `unsafe`, raw pointer APIs, or unvalidated behavior, classify it as partial/failure, not success.

---

## 6. Supported MVP Scope

This prototype should initially target **function-level** and **small-module-level** translation, not full industrial-scale project migration.

### Supported C Idioms for MVP

Implement robust support for these first:

| C Pattern | Rust Target |
|---|---|
| `T *arr, int len` read-only | `&[T]` |
| `T *arr, int len` mutated | `&mut [T]` |
| `T *out` output parameter | return value or tuple |
| return code + output parameter | `Result<T, E>` |
| nullable pointer | `Option<&T>` / `Option<&mut T>` |
| simple local `malloc/free` buffer | `Vec<T>` |
| single owned heap allocation | `Box<T>` |
| C boolean integer | `bool` |
| simple error constants | Rust error enum or `Result<T, i32>` |

### Unsupported or Future Work

For the MVP, do not attempt full support for:

- complex macros;
- untagged unions;
- function pointers;
- inline assembly;
- volatile memory access;
- custom allocators;
- setjmp/longjmp;
- pointer-to-integer casts;
- integer-to-pointer casts;
- complex aliasing;
- arbitrary linked data structures;
- external library-heavy code;
- full multi-file build-system migration.

These should be classified and reported clearly.

---

## 7. Safety Eligibility Classification

SafeMAP must classify every translation unit before attempting safe translation.

### Required Categories

Use these exact category names where possible:

```text
safe_translatable
safe_translatable_with_api_change
requires_safe_wrapper
requires_manual_refactor
unsafe_required
unsupported
```

### Category Meaning

#### `safe_translatable`

The unit can be translated to safe Rust without major API changes.

Example:

```c
int sum(int *arr, int len);
```

to:

```rust
pub fn sum(arr: &[i32]) -> i32
```

#### `safe_translatable_with_api_change`

The unit can be translated safely, but the public API should become more Rust-like.

Example:

```c
int parse_int(const char *s, int *out);
```

to:

```rust
pub fn parse_int(s: &str) -> Result<i32, ParseError>
```

#### `requires_safe_wrapper`

The unit contains operations that may require unsafe internally, but a safe Rust wrapper might be possible.

For the strict SafeMAP safe-first evaluation, this should not count as fully safe unless the accepted translated logic itself is safe.

#### `requires_manual_refactor`

The C source needs restructuring before safe Rust can be generated.

Example: deeply tangled pointer aliasing, unclear ownership, or unsafe global state.

#### `unsafe_required`

The operation inherently requires unsafe Rust.

Examples:

- FFI boundary calls;
- volatile MMIO;
- inline assembly;
- low-level representation reinterpretation.

#### `unsupported`

The current prototype does not handle the construct.

Examples:

- complex macros;
- untagged unions;
- function pointer dispatch;
- unsupported build configuration.

### Required Eligibility Checks

The classifier should inspect:

- pointer role;
- pointer nullability;
- array/buffer length relationship;
- mutability;
- aliasing risk;
- allocation ownership;
- return-code conventions;
- output parameters;
- global mutable state;
- external calls;
- macros;
- union usage;
- pointer arithmetic;
- casts;
- unsupported constructs.

---

## 8. C Static Analysis Requirements

The C analyzer should extract at least:

- functions;
- parameters;
- return types;
- pointer parameters;
- struct declarations;
- typedefs;
- enums;
- global variables;
- call relationships;
- array subscripting;
- dereferences;
- address-of operations;
- null checks;
- malloc/calloc/realloc/free calls;
- return statements;
- assignments to pointer targets;
- loops over array indices;
- macro usage indicators;
- external function calls.

### Pointer Classification

Each pointer should be classified into one or more roles:

```text
input_pointer
output_pointer
inout_pointer
nullable_pointer
array_pointer
mutable_array_pointer
string_pointer
owned_allocation
borrowed_view
opaque_external
function_pointer
pointer_arithmetic
unknown_pointer
```

### Example

For:

```c
int sum(int *arr, int len) {
    int total = 0;
    for (int i = 0; i < len; i++) {
        total += arr[i];
    }
    return total;
}
```

Expected facts:

```json
{
  "function": "sum",
  "pointers": [
    {
      "name": "arr",
      "role": ["array_pointer", "input_pointer"],
      "element_type": "int",
      "length_parameter": "len",
      "nullable": false,
      "mutated": false
    }
  ],
  "eligible_category": "safe_translatable"
}
```

---

## 9. Idiom Detection Requirements

The idiom detector should identify and report:

### 9.1 Pointer-Length Array

C:

```c
int sum(int *arr, int len);
```

Rust:

```rust
pub fn sum(arr: &[i32]) -> i32
```

If the array is mutated:

```rust
pub fn normalize(arr: &mut [i32])
```

### 9.2 Output Parameter

C:

```c
void get_value(int *out);
```

Rust:

```rust
pub fn get_value() -> i32
```

For multiple output parameters:

```rust
pub fn get_pair() -> (i32, i32)
```

### 9.3 Return Code + Output Parameter

C:

```c
int parse(const char *s, int *out);
```

Rust:

```rust
pub fn parse(s: &str) -> Result<i32, ParseError>
```

For MVP, `Result<T, i32>` is acceptable if no error enum is inferred:

```rust
pub fn parse(s: &str) -> Result<i32, i32>
```

### 9.4 Nullable Pointer

C:

```c
int maybe_read(int *p) {
    if (p == NULL) return 0;
    return *p;
}
```

Rust:

```rust
pub fn maybe_read(p: Option<&i32>) -> i32
```

### 9.5 Simple Allocation

C:

```c
int *make_array(int n) {
    int *arr = malloc(n * sizeof(int));
    ...
    return arr;
}
```

Rust:

```rust
pub fn make_array(n: usize) -> Vec<i32>
```

Only support this when ownership is clear.

---

## 10. Migration Plan Requirements

For every translation unit, produce a JSON migration plan in:

```text
plans/<unit_id>.json
```

Minimum schema:

```json
{
  "unit_id": "sum",
  "source_file": "examples/sum/sum.c",
  "function": "sum",
  "eligibility": "safe_translatable",
  "eligibility_reasons": [],
  "detected_idioms": [
    {
      "kind": "pointer_length_array",
      "pointer": "arr",
      "length": "len",
      "mutability": "immutable",
      "rust_type": "&[i32]"
    }
  ],
  "original_signature": "int sum(int *arr, int len)",
  "target_signature": "pub fn sum(arr: &[i32]) -> i32",
  "type_migrations": [
    {
      "c": "int *arr, int len",
      "rust": "arr: &[i32]",
      "reason": "arr is indexed from 0..len and not mutated"
    }
  ],
  "safety_constraints": [
    "no unsafe code",
    "no raw pointer public API",
    "compile with #![forbid(unsafe_code)]"
  ],
  "validation": {
    "compile": true,
    "unit_tests": "if_available",
    "differential_tests": "if_applicable",
    "clippy": true,
    "miri": "optional"
  }
}
```

Migration plans are the key research artifact. They must be readable and useful for evaluation.

---

## 11. LLM Integration Requirements

### Provider Abstraction

Do not hardcode a provider into business logic.

Use an abstraction similar to:

```python
class LLMClient:
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        ...
```

The first implementation can use an OpenAI-compatible API.

### Environment Variables

API keys must be read from environment variables.

Do not hardcode keys.

Required default:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Optional:

```bash
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4.1-mini"
```

The actual model name should be configurable.

### LLM Prompt Must Include

For safe-first translation, prompts should include:

- original C code;
- extracted static-analysis facts;
- detected idioms;
- migration plan;
- target Rust signature;
- explicit safety constraints;
- instruction to avoid `unsafe`;
- instruction to avoid raw pointers;
- instruction to preserve behavior;
- compiler errors during repair, if any.

### LLM Prompt Must Forbid

The prompt must explicitly forbid:

- `unsafe`;
- `*const`;
- `*mut`;
- `extern "C"` in safe translated logic;
- changing the target signature without permission;
- silently dropping behavior;
- using placeholder code;
- using `todo!()`, `unimplemented!()`, or `panic!()` unless the C behavior genuinely aborts.

---

## 12. Compiler-Guided Repair Requirements

The repair stage should:

1. run `cargo check`;
2. capture diagnostics;
3. categorize errors where possible;
4. pass the current Rust code, migration plan, and compiler errors to the LLM;
5. request a repair that preserves the safe target API;
6. reject repairs that introduce unsafe code;
7. limit repair attempts.

Recommended default:

```yaml
repair:
  enabled: true
  max_iterations: 3
  forbid_unsafe: true
```

### Repair Failure

If repair fails, record:

- final compiler errors;
- number of repair attempts;
- whether unsafe was attempted;
- failure category;
- suggested manual action.

Do not silently replace failed safe Rust with C2Rust output and call it success.

---

## 13. Validation Requirements

Validation should create:

```text
validation/results.json
```

### Required Validation Checks

- `cargo check`
- `cargo test` if tests are available
- `cargo clippy` if installed/enabled
- differential testing if applicable
- `cargo +nightly miri test` if enabled and available

### Miri Policy

Miri is optional.

If Miri is not installed, mark it as:

```json
"miri": {
  "status": "skipped",
  "reason": "miri_not_installed"
}
```

Do not fail the whole run merely because Miri is missing unless the config explicitly requires it.

### Differential Testing

Differential testing should compare the original C behavior and generated Rust behavior on the same inputs.

For MVP, support simple function signatures:

- integers;
- booleans;
- arrays/slices of integers;
- simple output values;
- simple strings if possible.

If differential testing is not applicable, record:

```json
"differential": {
  "status": "not_applicable",
  "reason": "unsupported_signature"
}
```

---

## 14. Metrics Requirements

SafeMAP must report metrics that support the research paper.

### Required Core Metric

```text
fully_safe_translation_unit_acceptance_rate
```

Definition:

```text
accepted fully safe units / total eligible units
```

### Required Metrics

Create metrics in:

```text
reports/metrics.json
```

Minimum fields:

```json
{
  "total_units": 0,
  "eligible_units": 0,
  "fully_safe_accepted_units": 0,
  "fully_safe_translation_unit_acceptance_rate": 0.0,
  "compile_success_units": 0,
  "test_pass_units": 0,
  "differential_pass_units": 0,
  "unsafe_blocks": {
    "baseline_c2rust": 0,
    "safemap_final": 0
  },
  "unsafe_functions": {
    "baseline_c2rust": 0,
    "safemap_final": 0
  },
  "raw_pointer_count": {
    "baseline_c2rust": 0,
    "safemap_final": 0
  },
  "raw_pointer_public_api_count": {
    "baseline_c2rust": 0,
    "safemap_final": 0
  },
  "idiom_migrations": {
    "pointer_length_array_to_slice": 0,
    "output_parameter_to_return": 0,
    "nullable_pointer_to_option": 0,
    "error_code_to_result": 0,
    "malloc_free_to_vec_or_box": 0
  },
  "failure_categories": {
    "unsupported": 0,
    "unsafe_required": 0,
    "requires_manual_refactor": 0,
    "repair_failed": 0,
    "validation_failed": 0
  }
}
```

### Important Reporting Rule

Report unsafe reduction, but do not use unsafe reduction alone as the main success metric.

The main success metric is fully safe accepted units.

---

## 15. Report Requirements

Generate:

```text
reports/report.md
reports/metrics.json
reports/comparison.csv
```

### report.md Should Include

1. Project name and run ID.
2. Input path.
3. Config summary.
4. Dependency availability.
5. Number of C files/functions analyzed.
6. Eligibility classification summary.
7. Idiom detection summary.
8. Baseline C2Rust metrics.
9. SafeMAP final metrics.
10. Fully safe accepted units.
11. Units rejected or skipped.
12. Failure reasons.
13. Validation summary.
14. Comparison table.
15. Limitations.

### comparison.csv Should Include

At least:

```csv
unit_id,baseline,eligibility,generated,compile_status,test_status,differential_status,unsafe_blocks,raw_pointers,fully_safe_accepted,failure_reason
```

---

## 16. CLI Requirements

Keep existing CLI commands if already implemented.

Required commands:

```bash
safemap run --input examples/output_parameter --output results
```

```bash
safemap ingest --input examples/output_parameter --output work
safemap analyze-c --workdir work
safemap translate-baseline --workdir work
safemap analyze-rust --workdir work
safemap plan --workdir work
safemap rewrite --workdir work --config safemap.example.yaml
safemap repair --workdir work --config safemap.example.yaml
safemap validate --workdir work --config safemap.example.yaml
safemap report --workdir work
```

Required benchmark command:

```bash
safemap benchmark \
  --benchmarks examples \
  --output reports/benchmark_results.csv \
  --config safemap.example.yaml
```

Required modes:

```text
c2rust_only
llm_only
c2rust_llm_unguided
safemap_full
```

---

## 17. Run Directory Structure

SafeMAP should write outputs into timestamped run folders:

```text
results/.safemap/runs/<timestamp>-<project>-<id>/
```

Required files:

```text
project.json
analysis/c_analysis.json
analysis/translation_units.json
analysis/eligibility.json
plans/*.json
baseline/rust/
baseline/metrics.json
final/rust/
validation/results.json
reports/report.md
reports/metrics.json
reports/comparison.csv
logs/run.log
```

If a stage is skipped or fails, the run directory should still contain artifacts explaining what happened.

---

## 18. Configuration Requirements

Use YAML config.

Example:

```yaml
project:
  name: safemap

translation:
  mode: safemap_full
  use_llm: true
  forbid_unsafe: true
  allow_c2rust_fallback_as_success: false
  max_units: null

eligibility:
  reject_unknown_pointers: true
  reject_unresolved_aliasing: true
  reject_unions: true
  reject_function_pointers: true
  reject_inline_asm: true

llm:
  provider: openai_compatible
  model: gpt-4.1-mini
  base_url: https://api.openai.com/v1
  temperature: 0.1
  max_tokens: 4096

repair:
  enabled: true
  max_iterations: 3
  forbid_unsafe: true

validation:
  cargo_check: true
  cargo_test: true
  clippy: true
  miri: false
  differential_testing: true

reporting:
  write_markdown: true
  write_json: true
  write_csv: true
```

### Critical Config Rule

If:

```yaml
translation:
  allow_c2rust_fallback_as_success: false
```

then C2Rust fallback must never be counted as a successful SafeMAP safe translation.

---

## 19. Manual Dependencies the User Must Install

These steps assume Ubuntu/Debian Linux.

### 19.1 Install System Packages

```bash
sudo apt update

sudo apt install -y \
  build-essential \
  clang \
  llvm \
  llvm-dev \
  libclang-dev \
  cmake \
  libssl-dev \
  pkg-config \
  git \
  curl \
  bear \
  python3 \
  python3-venv \
  python3-pip
```

### 19.2 Install Rust

Official Rust installation:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

Add useful Rust components:

```bash
rustup component add clippy rustfmt
```

Verify:

```bash
rustc --version
cargo --version
cargo clippy --version
```

### 19.3 Optional: Install Miri

Miri is optional for initial development.

```bash
rustup toolchain install nightly
rustup +nightly component add miri
cargo +nightly miri setup
```

Verify:

```bash
cargo +nightly miri --version
```

If Miri setup fails, SafeMAP should still run with Miri disabled.

### 19.4 Install C2Rust

```bash
cargo install --locked c2rust
```

If LLVM detection fails:

```bash
LLVM_CONFIG_PATH="$(which llvm-config)" cargo install --locked c2rust
```

Verify:

```bash
c2rust --version
```

### 19.5 Verify Bear

```bash
bear --version
```

If Bear is unavailable, SafeMAP should still support single-file mode and record project build recovery as skipped/limited.

---

## 20. Python Environment Setup

From the SafeMAP repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev,rust-analysis]"
```

Verify:

```bash
safemap --help
pytest
```

If the current expected result is `24 passed`, preserve that and add more tests as features are added.

---

## 21. LLM Setup

SafeMAP uses an OpenAI-compatible API.

The user must set:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Optional:

```bash
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="your-model-name"
```

Do not commit `.env` files or secrets.

If LLM credentials are missing:

- ingestion should still work;
- analysis should still work;
- baseline C2Rust should still work if installed;
- planning should still work;
- rewrite/repair should be skipped or marked failed gracefully;
- no unit should be counted as fully safe accepted merely because LLM was unavailable.

---

## 22. Example Runs

### 22.1 Full Run

```bash
safemap run \
  --input examples/output_parameter \
  --output results \
  --config safemap.example.yaml
```

Inspect:

```bash
find results/.safemap/runs -maxdepth 1 -type d | sort
cat results/.safemap/runs/<latest-run>/reports/report.md
```

### 22.2 No LLM Mode

```yaml
translation:
  use_llm: false
```

Expected behavior:

- ingestion works;
- analysis works;
- C2Rust baseline may run;
- migration plans are generated;
- final safe rewriting is skipped;
- report clearly says no LLM rewrite was performed.

### 22.3 Benchmark Run

```bash
safemap benchmark \
  --benchmarks examples \
  --output reports/benchmark_results.csv \
  --config safemap.example.yaml
```

---

## 23. Testing Requirements

Add tests for each major capability.

### Required Test Areas

- C function extraction;
- pointer classification;
- idiom detection;
- eligibility classification;
- migration plan generation;
- prompt construction;
- unsafe-code detection in Rust;
- raw pointer counting;
- compiler error parsing;
- validation result schema;
- report generation.

### Example Test Cases

Create or preserve examples under:

```text
examples/
  simple_sum/
  output_parameter/
  nullable_pointer/
  pointer_length_array/
  mutable_buffer/
  error_code_result/
  malloc_free/
  unsupported_union/
  unsupported_function_pointer/
```

Each example should include:

- C source file;
- optional C test/harness;
- expected analysis facts;
- expected migration plan;
- expected eligibility category.

---

## 24. Coding Instructions for Codex

When modifying the repository:

1. Inspect the existing code before rewriting.
2. Preserve the existing CLI unless there is a strong reason to change it.
3. Add features incrementally.
4. Add tests for every new module or behavior.
5. Keep artifacts stable and easy to inspect.
6. Do not hardcode machine-specific paths.
7. Do not hardcode API keys.
8. Make missing external tools non-fatal where possible.
9. Prefer structured JSON outputs over plain text for machine-readable artifacts.
10. Keep Markdown reports human-readable.
11. Keep the research framing honest:
    - accepted safe Rust is strict;
    - unsupported code is reported;
    - C2Rust baseline is not a SafeMAP success by default.

---

## 25. Suggested Implementation Priority

### P0 — Align Project Semantics

- Update README/config/report wording so SafeMAP is safe-first.
- Ensure reports distinguish:
  - C2Rust baseline;
  - partially safer output;
  - fully safe accepted output.

### P1 — Eligibility Classifier

Implement or strengthen:

- pointer role classifier;
- unsupported feature detector;
- safety eligibility categories.

### P2 — Migration Planner

Implement robust JSON plans for MVP idioms.

### P3 — Safe Rust Synthesis

Generate safe Rust using migration plans and LLM prompts.

Ensure generated crate includes:

```rust
#![forbid(unsafe_code)]
```

### P4 — Compiler Repair

Repair compiler errors without allowing unsafe.

Reject repairs that introduce unsafe.

### P5 — Validation

Run:

- cargo check;
- cargo test;
- Clippy;
- optional Miri;
- basic differential testing.

### P6 — Reporting

Generate:

- report.md;
- metrics.json;
- comparison.csv.

Make “fully safe accepted units” the main metric.

### P7 — Benchmarks

Run across examples and compare modes:

- `c2rust_only`
- `llm_only`
- `c2rust_llm_unguided`
- `safemap_full`

---

## 26. Acceptance Criteria for MVP

The MVP is acceptable when:

1. `pytest` passes.
2. `safemap --help` works.
3. `safemap run --input examples/output_parameter --output results --config safemap.example.yaml` produces a complete run folder.
4. Reports include eligibility classification and safe acceptance metrics.
5. At least 5 C idiom examples are analyzed correctly.
6. At least 3 examples are translated into Rust that compiles with `#![forbid(unsafe_code)]`.
7. C2Rust baseline metrics are reported separately.
8. Failed/unsupported examples are classified honestly.
9. Missing C2Rust, Miri, Bear, or LLM credentials produce clear skipped/failed stage records instead of unhandled crashes.
10. No final safe accepted unit contains unsafe Rust.

---

## 27. Paper-Oriented Outputs

The tool should generate results that can be used directly in the research paper.

Required tables:

1. Benchmark summary.
2. Eligibility classification counts.
3. Safe translation success by idiom.
4. Baseline comparison:
   - C2Rust-only;
   - LLM-only;
   - C2Rust+LLM unguided;
   - SafeMAP full.
5. Unsafe/raw-pointer reduction.
6. Failure category distribution.
7. Validation results.

The report should make it easy to write statements like:

```text
SafeMAP generated fully safe Rust for X/Y eligible units.
C2Rust generated unsafe Rust for Z/Y units.
LLM-only translation failed to compile for A units.
SafeMAP rejected B units due to unresolved aliasing, unsupported unions, or external FFI dependencies.
```

Do not invent these values. They must come from actual metrics.

---

## 28. Final Guidance

The project should be implemented as a rigorous research prototype.

The goal is not to make every C program translate.

The goal is to show that:

1. safe-first translation is possible for a meaningful subset of C;
2. static analysis improves LLM-guided translation;
3. strict safe acceptance is more meaningful than unsafe-code reduction alone;
4. unsupported code can be classified clearly for manual review.

If there is a conflict between earlier notes and this file, follow this file.

# SafeMAP Resubmission Evaluation Protocol

Protocol version: `safemap.resubmission_protocol.v2`

Status: **draft — not sealed.** Seal (date and commit) before any SafeMAP
execution on the v2 held-out corpus.

## Why a new experiment

The v1 frozen held-out run (`safemap.conference_protocol.v1`, implementation
`b2f455c`) accepted 0/142 units, and all three raw C2Rust attempts failed. v1
requires that corrections after unsealing be "disclosed, versioned as a new
experiment, and evaluated on a newly selected test set". This protocol is that
experiment. The v1 corpus (inih, cJSON, libcsv) has been inspected and is now
**development and diagnostic data**; results on it must be labeled as such.

## Root causes found in the v1 run

Every item below independently forced the v1 outcome to zero. Each was traced
in the archived v1 artifacts under `reports/publication/conference/raw/`.

| # | Defect | v1 effect |
|---|--------|-----------|
| 1 | Signature planner mapped C types incorrectly (`cJSON *` returned as `cJSON`, `char *` as `i8`, `void *` as `()`, `char **` as `&mut i8`) | Plans demanded uncompilable or wrong interfaces |
| 2 | `nullable_read` rule fired for *any* function with a nullable pointer and emitted `Some(v) => *v` regardless of the body; scalar-return rules matched the first `return` anywhere; `(const char *)` passed the arithmetic check | 15 of 17 generated units were template stubs, one was raw C |
| 3 | Struct definitions in project headers were never collected, and structs with pointer fields were silently dropped | Crates referenced undefined types |
| 4 | Acceptance was all-or-nothing per project | One failing function zeroed every unit |
| 5 | C2Rust header shims shadowed the real libc headers (`FILE`, `memcpy`, `sprintf` vanished); host glibc 2.44 also crashes C2Rust's LLVM 14 exporter; C2Rust output was put in `src/<name>.rs` with no `lib.rs`; raw output needs nightly | All C2Rust attempts failed; the plan-guided LLM path, which built on C2Rust output, never ran |
| 6 | The behavioral harness covered only scalars, dot products, fixed arrays, and scalar-field structs | Correct code for strings, buffers, or nullable pointers could not be validated |

## Method changes (v2)

1. **Sound interface planning.** `plan_signature` reports every C type it
   cannot map to a safe, testable Rust type (opaque `void *`/`FILE *`,
   pointer-to-pointer, returned aliasing pointers, structs with unresolved
   pointer ownership). A unit with any such issue is rejected at planning with
   the issue recorded in its plan (`signature_issues`); no signature is
   fabricated.
2. **Scalar-field projection.** A struct pointer parameter may be planned as a
   Rust struct holding only the struct's scalar fields when every use of the
   pointer in the unit is a scalar-field access, a NULL/truth test, or a bare
   argument to a project function whose matching parameter satisfies the same
   condition (checked recursively). Pointer fields are never observed by such a
   unit, so omitting them cannot change its behavior.
3. **Mutable global state** makes a function `requires_manual_refactor`.
4. **Exact deterministic rules.** Rules that render a single expression require
   the whole body to be that statement; expressions may reference only
   parameters and called functions.
5. **Unit engine.** Units are processed in dependency order. Each unit is
   synthesized by an exact deterministic rule if one applies, otherwise by a
   plan-guided LLM request (C function, referenced macros/enums/const tables,
   Rust struct definitions, accepted callee signatures, analysis facts, and
   migration plan), followed by up to `max_repair_attempts` compiler-feedback
   repairs. A unit is admitted to the crate only if it has the planned
   signature, passes the policy check (no `unsafe`, raw pointers, `extern`,
   or placeholders), and compiles together with the units already admitted.
   A unit whose internal callee was not admitted is `dependency_missing`.
6. **Per-unit acceptance.** A unit is accepted iff it was admitted, the final
   crate compiles and passes clippy under `#![forbid(unsafe_code)]`, its
   interface exposes no raw pointers, and its per-unit differential test
   passes.
7. **Per-unit differential testing (`safemap-unit-harness-v1`).** Inputs are
   generated once per unit from a fixed seed, including integer literals mined
   from the C body and their neighbours, and embedded as literal tables in a C
   harness and a Rust harness. The C harness includes the original translation
   unit and runs under ASan + UBSan with `-fno-sanitize-recover=all`. Return
   values and every value written through a mutable parameter are compared
   exactly (floating point by bit pattern, strings byte by byte). An input on
   which the C oracle aborts with a sanitizer report has no defined C behavior;
   it is excluded and counted. A defined C abort/exit must be matched by a Rust
   panic. A unit needs at least 50% defined inputs. The Rust harness is built
   with overflow checks enabled.
8. **C2Rust baseline** runs in the pinned image `docker/c2rust/Dockerfile`
   (Ubuntu 22.04, LLVM/Clang 14, C2Rust 0.22.1) and is compiled there with
   `nightly-2026-03-01`. The image ID is recorded in each run's
   `tool_versions.json`.
9. **LLM client** retries HTTP 429/5xx and network errors with exponential
   backoff (at most 10 retries, each wait capped at 120 s).

## Configurations

Configuration file: `research/resubmission_evaluation.yaml`
(`temperature: 0`, `max_repair_attempts: 3`, 1,000 differential inputs,
seed `20260728`). Every LLM configuration, SafeMAP and baselines alike, uses
`gemini-3.5-flash-lite`, pinned in the config; the frozen runner refuses
`SAFEMAP_MODEL`/`SAFEMAP_BASE_URL` overrides. (`gemini-3.5-flash` was
persistently unavailable with HTTP 503 during development.) A sustained
provider outage aborts the run instead of being scored as a unit failure.

The one-shot `llm_only` baseline receives the project headers as well as the
`.c` file, and the model's full output budget (65,536 tokens, 900 s); v1 gave
it only the `.c` file and 8,192 tokens. Its functions are scored with the same
per-unit harness against SafeMAP's planned interfaces; a function with another
signature is recorded as `interface_mismatch`.

| Mode | Role |
|------|------|
| `safemap_guided` | Primary: rules + plan-guided LLM + repair, unit engine |
| `safemap_deterministic` | Rules only (no LLM), unit engine |
| `safemap_guided_unguided_prompt` | Same loop and signatures; analysis facts and plan withheld from prompts |
| `safemap_guided_without_validation_feedback` | No compiler-feedback repair |
| `safemap_guided_without_{pointer_roles,safe_signatures,dependency_grouping,idiom_plans}` | Component ablations |
| `c2rust_only` | Raw C2Rust (pinned image); reported for compile rate and unsafe counts |
| `llm_only` | One-shot whole-file LLM translation, same acceptance policy |

## Held-out corpus (v2)

### Selection rule (fixed before inspection of any SafeMAP output)

A library qualifies if all of the following hold:

1. Public Git repository, pinned to an immutable commit; OSI-approved license.
2. Its production code is one `.c` file plus project headers, compiling with
   `clang -c` against libc only.
3. 150–3,500 physical lines in the `.c` file.
4. Not part of any SafeMAP development or diagnostic set (`examples/`,
   `case_studies/`, `external_corpus/llvm_test_suite_misc/`, inih, cJSON,
   libcsv).
5. Not chosen on the basis of any SafeMAP output.

All function definitions in each selected production `.c` file are retained;
there is no function-level filtering.

### Selected libraries

Confirmed by the authors on 2026-10-17 and recorded in
`research/resubmission_corpus_manifest.json` (repository, revision, file
hashes, license):

| Library | Production file | Lines | License |
|---------|-----------------|-------|---------|
| kgabis/parson | `parson.c` | 2,494 | MIT |
| antirez/sds | `sds.c` | 1,328 | BSD-2-Clause |
| codeplea/tinyexpr | `tinyexpr.c` | 1,025 | Zlib |
| rxi/microtar | `src/microtar.c` | 376 | MIT |

Each compiles with `clang -c` against libc. `sds.c` contains a test driver
under `#ifdef SDS_TEST_MAIN`; it is not compiled by default and is therefore
not part of the corpus.

### Sequencing

1. Commit all implementation changes; full unit test suite green.
2. Run development evaluation (examples, case studies, LLVM corpus, v1 corpus
   as diagnostic).
3. Seal this protocol and the corpus manifest; record the freeze
   (`research/implementation_freeze.json`, new record) with commit, tool
   versions, image ID, model name, and hashes.
4. Fetch the v2 corpus into a fresh directory and run every configuration
   once. No implementation change after this point; any later correction is a
   v3 experiment on another new corpus.
5. Independent eligibility labels: two reviewers label the v2 functions
   without seeing SafeMAP's decisions; adjudicate disagreements.

## Reporting

Report per corpus: units, candidate-safe, planned, type-mapping rejections (by
reason), admitted (compiled), behaviorally validated/accepted, failure
categories, undefined-behavior inputs excluded, LLM calls, tokens, retries,
and repair attempts. Report v1 results unchanged alongside v2, and label v1
corpus re-runs as diagnostic.

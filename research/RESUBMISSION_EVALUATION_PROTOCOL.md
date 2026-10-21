# SafeMAP Resubmission Evaluation Protocol

Protocol version: `safemap.resubmission_protocol.v2`

Status: **sealed 2026-10-19**, before any SafeMAP execution on the v2
held-out corpus. The implementation freeze record
(`research/implementation_freeze_v2.json`) names the sealed commit and hashes
this file, the corpus manifest, and the configuration.

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
it only the `.c` file and 8,192 tokens. Because every translation is tested
through the planned Rust interfaces, the baseline is given the same task as
SafeMAP in a single request: translate the planned functions, with the
planned public signatures (C names kept; a program's `main` keeps Rust's
entry-point signature and is not listed) and the Rust struct definitions
those signatures use, private helpers allowed. It receives none of SafeMAP's
analysis facts, migration plans, rules, or repair loop. Its output
is scored as a library (top-level functions made public; the code is not
otherwise changed) with the same per-unit harness. A function that still has
another signature is recorded as `interface_mismatch`. The contribution of
signature planning itself is measured by the `without_safe_signatures`
ablation.

| Mode | Role | Corpus |
|------|------|--------|
| `safemap_guided` | Primary: rules + plan-guided LLM + repair, unit engine | v2 held-out |
| `safemap_deterministic` | Rules only (no LLM), unit engine | v2 held-out |
| `c2rust_only` | Raw C2Rust (pinned image); reported for compile rate and unsafe counts | v2 held-out |
| `llm_only` | One-shot whole-file LLM translation, same acceptance policy | v2 held-out |
| `safemap_guided_unguided_prompt` | Same loop and signatures; analysis facts and plan withheld from prompts | development |
| `safemap_guided_without_validation_feedback` | No compiler-feedback repair | development |
| `safemap_guided_without_{pointer_roles,safe_signatures,dependency_grouping,idiom_plans}` | Component ablations | development |

The six ablations are not run on the v2 held-out corpus; it is evaluated
only with the four configurations above, so that the held-out LLM run fits
the provider's request quota. The ablations are run once with the frozen
implementation on the v1 corpus (inih, cJSON, libcsv) and reported as
**development data**, not as held-out results.

### Request quota

The evaluation uses the provider's free tier (500 requests per day for the
pinned model). When a request is still refused after the client's retries,
the run stops instead of scoring the unit. The stage then waits for the
reset time the provider reports and resumes. Each finished (project, mode)
result is checkpointed and reused, so it is never requested again. An
interrupted (project, mode) run is discarded and re-run from the start. A
held-out stage may therefore span several quota windows; each wait is
recorded in its `stage_manifest.json`.

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

### Amendment 1: held-out extension (2026-10-19)

Decided **after** results on microtar, parson, and sds were seen, because four
libraries are a small sample. To keep the extension independent of those
results:

- The same selection rule was applied to a fresh candidate screen; every
  qualifying candidate is listed in
  `research/resubmission_corpus_extension_manifest.json`, and the authors chose
  six of the nine for domain diversity before any SafeMAP execution on them.
- The implementation, configuration, and modes are unchanged (no file under
  `safemap/` or `research/resubmission_evaluation.yaml` differs from the sealed
  freeze commit); only the corpus is added.
- Results are reported for the original four libraries and for the extension
  separately, and then pooled.

| Library | Production file | Lines | License |
|---------|-----------------|-------|---------|
| udp/json-parser | `json.c` | 1,186 | BSD-2-Clause |
| kokke/tiny-regex-c | `re.c` | 528 | Unlicense |
| kokke/tiny-AES-c | `aes.c` | 572 | Unlicense |
| h2non/semver.c | `semver.c` | 638 | MIT |
| cofyc/argparse | `argparse.c` | 395 | MIT |
| mpaland/printf | `printf.c` | 914 | MIT |

### Amendment 2: plain one-shot baseline (2026-10-20)

Decided **after** all v2 results were seen, because the `llm_only` baseline
receives SafeMAP's planned interfaces and so does not show what an LLM
achieves without them. One configuration is added, run once on all ten
held-out libraries by `scripts/run_plain_llm_baseline.py`:

- `llm_only` with the planned signatures and struct definitions removed from
  the prompt (the frozen code's own no-interface prompt: C sources and the
  safety rules only). Scoring is unchanged: functions are tested through the
  planned interfaces, and one with any other signature is
  `interface_mismatch`.
- The script refuses to run unless `safemap/` and the configuration are
  identical to the freeze commit. No other mode, input, or setting changes.
- The result is reported as an added baseline, marked as decided after the
  results were seen.
- Like the other LLM configurations, it is run three times (output
  directories `plain-*`, `plain-rep2-*`, `plain-rep3-*`); the repeats were
  added on 2026-10-21, after the first run was seen.

### Post-hoc analyses (not part of the sealed evaluation)

These analyses do not change any reported held-out result. They are labeled
post-hoc wherever they appear.

- **Lint sensitivity** (`scripts/posthoc_lint_sensitivity.py`): re-scores
  the frozen tinyexpr crate with only `clippy::approx_constant` allowed, using
  the unchanged crate checks and per-unit harness on a copy of the run.
- **Survivor classification**: every surviving mutant is classified by hand
  as equivalent, input gap, or observation gap.

### Repeated LLM runs

LLM output can vary across requests even at temperature 0. The `v2-llm` stage
(`safemap_guided`, `llm_only`) is therefore run three times on every held-out
library with identical inputs, each into its own output directory; results
report the run-to-run range. The first run is the primary result.

### Sequencing

1. Commit all implementation changes; full unit test suite green.
2. Run development evaluation (examples, case studies, LLVM corpus, v1 corpus
   as diagnostic).
3. Seal this protocol and the corpus manifest; record the freeze
   (`research/implementation_freeze.json`, new record) with commit, tool
   versions, image ID, model name, and hashes.
4. Fetch the v2 corpus into a fresh directory and run each held-out
   configuration once (`v2-non-llm`, then `v2-llm`; an interrupted stage is
   continued with `--resume`). Run the ablations on the v1 corpus with the
   same frozen implementation (stage `v2-ablation`). No implementation change after this point; any
   later correction is a v3 experiment on another new corpus.

No independent eligibility labels are collected for v2. The evaluation
therefore makes no claim about the precision or recall of SafeMAP's
eligibility decisions; it reports those decisions as counts, and the
correctness of translations rests only on compilation, the safety policy, and
the per-unit differential test.

## Reporting

Report per corpus: units, candidate-safe, planned, type-mapping rejections (by
reason), admitted (compiled), behaviorally validated/accepted, failure
categories, undefined-behavior inputs excluded, LLM calls, tokens, retries,
and repair attempts. Report v1 results unchanged alongside v2, and label v1
corpus re-runs as diagnostic.

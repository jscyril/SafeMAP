# SafeMAP Conference Evaluation Protocol

Protocol version: `safemap.conference_protocol.v1`

Sealed: 2026-07-27, before running SafeMAP on the conference held-out corpus.

## Research claim

SafeMAP is evaluated as an auditable safe-first translation pipeline. The
evaluation separates:

1. a static candidate decision;
2. whether the current deterministic synthesizer implements a matching rule;
3. whether Rust was generated;
4. whether the generated crate satisfies the Rust-safety policy; and
5. whether behavioral validation passed.

`candidate_safe` is a screening result. It is not a proof that safe translation
exists and must not be described as such.

## Data separation

### Regression and development data

- `examples/`: authored regression examples.
- `case_studies/`: authored module-composition regression cases.
- `external_corpus/llvm_test_suite_misc/`: previously observed external
  characterization data. Because its outcomes are known and its accepted helper
  has an authored harness, it is development data for future synthesis work,
  not a held-out test set.

Rules may be developed and debugged on these inputs. Results on these datasets
must be labeled development or regression results in the paper.

### Frozen held-out data

The held-out sources are defined by `research/heldout_corpus_manifest.json`.
They are three independently maintained C libraries:

- inih;
- cJSON; and
- libcsv.

The source repositories, immutable revisions, production source/header files,
licenses, line counts, and SHA-256 hashes were fixed before SafeMAP execution.
All function definitions in the listed production source files are retained.
There is no function-level filtering based on SafeMAP output.

The source files must not be copied into the evaluation directory, analyzed by
SafeMAP, or used to modify synthesis rules until an implementation freeze record
has been created. `scripts/prepare_conference_heldout.py` enforces this gate.

## Evaluation stages

### Stage A: implementation development

Permitted inputs are the authored suites and LLVM development corpus. During
this stage:

- add explicit candidate and synthesis-support decisions;
- record the analyzer backend;
- implement generic validation;
- add component-level ablations;
- expand deterministic rules using development inputs only; and
- keep all regression tests green.

### Stage B: implementation freeze

Before held-out execution:

1. commit all implementation, configuration, and development-test changes;
2. run the full unit and development evaluation;
3. record the exact Git commit and tool versions in
   `research/implementation_freeze.json`;
4. set its status to `frozen`; and
5. make no translation-rule changes after inspecting held-out outcomes.

`scripts/freeze_conference_implementation.py` enforces a clean committed
worktree, a non-placeholder baseline model, zero-temperature baseline sampling,
at least 1,000 differential cases, enabled C sanitizers, passing tests, and
hashes of the protocol, corpus manifests, configuration, and selected
development artifacts.

Corrections after unsealing must be disclosed, versioned as a new experiment,
and evaluated on a newly selected test set. The original result remains part of
the audit record.

### Stage C: independent eligibility labels

At least two reviewers label held-out functions without seeing SafeMAP's
decision. Labels use:

- `candidate_safe`;
- `manual_refactor_required`;
- `unsafe_required`; and
- `unknown`.

Reviewers also record construct tags, rationale, and confidence. Disagreements
are retained, adjudicated separately, and reported with raw agreement and
Cohen's kappa. SafeMAP eligibility precision and recall are computed against
the adjudicated labels, with `unknown` excluded from binary precision/recall and
reported separately.

`scripts/evaluate_eligibility_labels.py` enforces two labels per function,
hashes every label and decision input, and exports individual false positives,
false negatives, construct-stratified disagreements, and analyzer-backend
strata.

`implemented_support` is deliberately not a human eligibility label. It is a
separate, mechanically recorded property of the current synthesizer.

### Stage D: held-out execution

Run the frozen implementation once on all retained production functions. Save:

- source and configuration hashes;
- analyzer backend and diagnostics;
- every unit decision and reason;
- synthesis rule selection;
- generated Rust;
- validation commands;
- deterministic and randomized inputs;
- seeds;
- C and Rust outputs;
- compiler diagnostics;
- Miri, ASan, and UBSan status where applicable; and
- wall-clock timings.

No result-based exclusions are allowed.

`scripts/characterize_corpus.py` exports the project and function rows plus
LOC, cyclomatic-complexity, parameter, pointer-density, construct, and analyzer
backend distributions.

## Primary outcome cascade

For each dataset and function role, report:

1. total units;
2. `candidate_safe` units;
3. `implemented_support` units;
4. generated units;
5. compiling units;
6. policy-safe units;
7. behaviorally validated policy-safe units; and
8. complete projects/modules.

Function roles are:

- `declared_target`;
- `helper`;
- `entry_point`; and
- `other`.

The primary effectiveness metric is behaviorally validated policy-safe units
divided by retained held-out units. Conditional rates, including generation
given candidate status, are secondary and must show their denominators.

## Safety and behavioral policies

Policy-safe Rust must:

- compile with `#![forbid(unsafe_code)]`;
- contain no unsafe blocks, unsafe functions, unsafe impls, or extern-C blocks;
- expose no raw-pointer public API; and
- contain the planned generated unit.

Behaviorally validated policy-safe Rust must additionally pass an applicable
C-versus-Rust oracle. `skipped` and `not_applicable` are never counted as
behaviorally validated.

Randomized validation records the generator, seed, concrete inputs, C output,
Rust output, exit status, and timeout. Original C executions should run under
ASan and UBSan where supported; cases with observed source undefined behavior
are reported separately and are not treated as trustworthy equivalence oracles.

## Baselines and ablations

Raw C2Rust remains a strict-policy calibration, not the sole competitive
baseline. A conference result must include at least one runnable safe-output
baseline on the same retained units.

The planned competitive baseline is `llm_only`: direct C-to-safe-Rust
translation without SafeMAP analysis or planning. Each run stores the exact
prompt and response, requested and returned model names, temperature, maximum
tokens, measured input/output tokens, timeout, retry index, and failures in
`logs/direct_llm_call.json`. The model configuration is frozen before held-out
execution, and failed or rejected responses remain in the result denominator.

The frozen baseline model is `gemini-3.5-flash-lite`, accessed through Google
AI Studio's OpenAI-compatible endpoint. It was selected because Google lists
the stable model as available without input/output token charges on the free
tier as of the freeze date. The experiment makes at most one request per held-
out project and performs no result-dependent retries. A quota, rate-limit,
timeout, refusal, truncation, or malformed response remains a baseline failure;
SafeMAP's deterministic result never depends on the external service. Free-tier
requests may be retained by the provider under its published data-use terms, so
only the already-public pinned C sources are sent.

Provider facts were checked against Google's official documentation before the
freeze:

- OpenAI-compatible endpoint and authentication:
  <https://ai.google.dev/gemini-api/docs/openai>
- model identifiers and lifecycle:
  <https://ai.google.dev/gemini-api/docs/models>
- free-tier pricing and data-use table:
  <https://ai.google.dev/gemini-api/docs/pricing>
- project-level quota behavior:
  <https://ai.google.dev/gemini-api/docs/rate-limits>

Component ablations remove one factor at a time:

- pointer-role evidence;
- safe-signature generation;
- dependency grouping;
- idiom-plan evidence; and
- validation feedback.

The existing mode that removes all structured guidance is retained only as a
pipeline dependency check.

## Reporting rules

- Never combine authored/development and held-out acceptance rates.
- Never call `candidate_safe` proof of translatability.
- Never count skipped behavioral validation as a behavioral pass.
- Report entry points separately from declared targets and helpers.
- Publish raw rows, labels, generated outputs, validation records, exclusions,
  and scripts.
- Regenerate tables from frozen CSV/JSON artifacts; do not hand-edit metrics.

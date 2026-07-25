# SafeMAP Research TODO and Status

Last audited: 2026-07-24

This file is the working research TODO for SafeMAP. It summarizes what the
current repository supports, what evidence exists for a paper, and what should
be done before making publication claims.

## Current Verdict

SafeMAP is good enough to start writing the paper. It is not yet good enough for
a strong publication submission without more evaluation cleanup and claim
tightening.

The current artifact supports a conservative workshop/short-paper style claim:

> SafeMAP is a safe-first C-to-Rust migration prototype that generates fully
> safe Rust for a restricted, statically identifiable subset of C functions and
> module-shaped examples. It rejects unsupported constructs explicitly and
> evaluates accepted output under `#![forbid(unsafe_code)]`, raw-pointer API
> checks, compilation, and available behavioral validation.

Do not claim:

- full automatic C-to-Rust migration;
- production readiness;
- support for arbitrary C projects;
- formal semantic equivalence;
- LLM effectiveness (LLM experiments are excluded from the paper);
- success based only on unsafe-code reduction.

## Verified Local Evidence

- Test suite: `116 passed` with `pytest`.
- Microbenchmarks: `40` example projects under `examples/`.
- Case studies: `5` authored module-shaped projects under `case_studies/`.
- External corpus: `10` outcome-blind programs from LLVM test-suite
  `SingleSource/Benchmarks/Misc`, pinned to commit
  `6cdc54e005552e3444fa7402cd18a6e4b6db195d`.
- Canonical, trackable publication artifacts:
  - `reports/publication/final/`
  - `reports/publication/case-studies/`
  - `reports/publication/external-corpus/`
  - `reports/publication/c2rust-only/`
  - `reports/publication/ablation/`
  - `reports/publication/combined_evaluation.md`
  - `reports/publication/artifact_metadata.json`
  - `reports/publication/reproduction_manifest.json`
- SafeMAP-only microbenchmark result:
  - rows: `40`
  - accepted units: `37 / 76`
  - fully safe unit acceptance rate: `0.487`
  - declared target functions accepted: `36 / 40`
  - target-function acceptance rate: `0.900`
- SafeMAP-only case-study result:
  - rows: `5`
  - accepted units: `15 / 20`
  - fully safe unit acceptance rate: `0.750`
  - declared target functions accepted: `15 / 15`
  - each case-study row passed differential validation
- Deterministic external-corpus result:
  - rows: `10`
  - C LOC: `589`
  - analyzed functions: `32`
  - accepted units: `1 / 22`
  - fully safe unit acceptance rate: `0.045`
  - `9` rows produced no supported deterministic synthesis
  - the accepted `mandel_2::sqr` unit passes Cargo check, Cargo test, Clippy,
    and a reviewed contextual harness against the retained LLVM stdout and
    exit-code oracle
- C2Rust-only baseline result:
  - rows: `40`
  - accepted units: `0 / 76`
  - the canonical CSV now uses the same denominator as deterministic SafeMAP
- Static-guidance ablation:
  - uses the same analyzer-derived denominator as the deterministic main run;
  - withholds classifications, safe signatures, and migration plans from
    synthesis;
  - uses neither C2Rust nor an external model;
  - publication artifacts are regenerated from this explicit mode.
- Paper draft directory inspected:
  - `/mnt/data/college/research/my_paper/main.tex`
  - `/mnt/data/college/research/my_paper/tables/*.tex`
  - `/mnt/data/college/research/my_paper/references.bib`
  - `/mnt/data/college/research/my_paper/reference_inventory.md`

## Implemented Capabilities

### Project Pipeline and Artifacts

- Ingests C projects and records project metadata.
- Runs C static analysis through libclang when available, with a regex fallback.
- Builds translation units and eligibility records.
- Creates structured migration plans.
- Runs C2Rust as a baseline/reference lane when configured.
- Runs deterministic safe synthesis for supported idioms.
- Runs optional LLM translation/rewrite paths through an OpenAI-compatible
  client.
- Writes timestamped run directories and durable report artifacts.
- Exports benchmark CSV, Markdown summaries, paper tables, and combined
  evaluation summaries.

### Safe Acceptance Policy

SafeMAP counts a unit as fully safe accepted only when the final Rust:

- compiles under `#![forbid(unsafe_code)]`;
- has no unsafe blocks, unsafe functions, unsafe impls, or `extern "C"` blocks
  in the final analyzed Rust;
- exposes no raw-pointer public API;
- contains the planned function in final output;
- passes cargo validation and available behavioral validation.

### Supported MVP Idioms

The current deterministic synthesizer handles these families in the benchmark
set:

- simple scalar integer returns;
- integer boolean idioms to `bool`;
- pointer-length arrays to Rust slices;
- mutable pointer-length buffers to mutable Rust slices;
- output parameters to return values;
- multiple output parameters to tuple returns;
- mutable scalar pointer updates to `&mut T`;
- return-code plus output-parameter to `Result<T, i32>`;
- nullable pointer reads to `Option<&T>` or `Result`;
- simple C string length inputs to `&str`;
- simple allocation idioms to `Box<T>` and selected `Vec<T>` patterns.

### Unsupported or Manual-Review Constructs

The analyzer rejects or reports:

- unions;
- function pointers;
- inline assembly;
- volatile access;
- setjmp/longjmp;
- pointer-integer casts;
- unresolved pointer ownership;
- unresolved aliasing risk;
- custom allocator behavior;
- complex macros and broad preprocessor behavior;
- larger multi-file build-system migration.

## Paper-Blocking TODOs

These should be done before treating the draft as submission-ready.

### P0: Reconcile Evaluation Numbers

- [x] Reconcile all paper-facing tables from the locally generated CSVs.
- [x] Resolve the C2Rust denominator mismatch; both canonical lanes now report
  over `76` eligible units.
- [x] Update repository test-count references to the current `116 passed`.
- [x] Add exact command lines and tool versions used for the final reported run
  through `scripts/reproduce_paper_artifacts.py`,
  `reports/publication/reproduction_manifest.json`, and
  `reports/publication/artifact_metadata.json`.
- [x] Run the updated reproduction script to create the clean
  `reports/publication/` snapshot in a fresh timestamped workspace.
- Commit the reviewed publication snapshot alongside the implementation.
- Do not hand-edit final metrics; regenerate tables from CSV artifacts.

### P0: Make the Paper Claim Match the Evidence

- Keep the main claim limited to a restricted safe-first subset.
- Make target-function acceptance and unit acceptance separate everywhere.
- Explain why accepted units can be `37 / 76` while declared target functions
  are `36 / 40`.
- Explain intentionally unsupported examples as rejection outcomes, not
  ordinary translation failures.
- Avoid positioning the current artifact as project-scale migration.
- Avoid using the Gemini subset as a full LLM baseline.

### P0: Refresh the Paper Draft

- [x] Update `/mnt/data/college/research/my_paper/main.tex`:
  - test count to the current `116`;
  - C2Rust denominator after reconciliation;
  - execution snapshot to mention generated report paths;
  - limitations around authored datasets, external synthesis coverage, skipped
    Miri, and the explicit exclusion of LLM experiments.
- [x] Keep the paper's test count synchronized with the current `116 passed`
  after adding publication and characterization tests.
- [x] Update `/mnt/data/college/research/my_paper/tables/*.tex` from generated
  report outputs.
- Replace placeholder author, affiliation, and email metadata.
- [x] Build the LaTeX PDF at least once with `pdflatex`/`bibtex` or a venue
  template and fix any citation/table issues.
  - 2026-07-21: built `/mnt/data/college/research/my_paper/main.pdf` with
    `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` after
    installing the needed Arch TeX packages.
  - 2026-07-22: rebuilt the five-page PDF after updating the test count and
    canonical publication-snapshot paths; the build completed without errors.
  - 2026-07-23: rebuilt the five-page PDF after adding the external-corpus
    result and revising the claims and methodology; the final log has no
    errors, undefined citations/references, or overfull boxes.
  - Citation coverage is clean: all 18 BibTeX entries, including the 16 local
    paper PDFs, C2Rust, and the LLVM test-suite source, are cited from
    `main.tex`.

### P0: Artifact Reproducibility

- [x] Add one documented script or Make target that regenerates:
  - SafeMAP final microbenchmark CSV/tables;
  - case-study CSV/tables;
  - C2Rust baseline CSV/tables;
  - combined paper summary;
  - LaTeX table fragments for the paper.
- [x] Record tool versions for Python, clang/libclang, Rust, Cargo, Clippy,
  C2Rust, and optional Miri in the generated `artifact_metadata.json`.
- [x] Add an artifact README explaining expected runtime, optional tools, and
  which failures are expected.
- [x] Ensure generated benchmark outputs do not accidentally include stale runs
  or temporary harness artifacts. Publication reproduction now uses a fresh
  timestamped work directory and copies an allowlisted artifact set into
  `reports/publication/`.

## High-Priority Research TODOs

### P1: Evaluation Breadth

- [x] Add a larger curated benchmark suite beyond authored toy examples.
  The pinned ten-program LLVM subset is stored under `external_corpus/`.
- [x] Include at least a small real-world or semi-realistic C corpus with clear
  selection criteria. The selection is outcome-blind, source-size bounded,
  architecture-neutral, hash-verified, and license-preserving.
- [x] Report LOC, number of functions, pointer density, unsupported-construct
  counts, and per-project complexity alongside unit acceptance. These fields
  are part of benchmark result schema v2 and its Markdown/LaTeX summaries.
- Add ablation rows if possible:
  - [x] analysis-guided deterministic SafeMAP;
  - [x] SafeMAP without static guidance;
  - [x] C2Rust-only strict policy.

### P1: LLM Baseline

- [x] Exclude LLM experiments and empirical LLM claims from the paper-facing
  artifact workflow. The optional implementation remains engineering scope.

### P1: Differential and Behavioral Validation

- [x] Consume the LLVM reference outputs for the accepted external unit and
  fail reference-backed library validation when no reviewed harness exists.
- [x] Record the reviewed external harness and its SHA-256 in the corpus
  manifest.
- Expand differential harness support beyond known benchmark names.
- Generate harnesses from function signatures and expected metadata instead of
  hard-coded project-name cases where feasible.
- Add multi-function and module-level differential tests beyond the current
  single-file/single-project path.
- Add fuzzing or randomized corpus generation with saved seeds and inputs.
- Record generated differential inputs and outputs as artifacts for auditing.
- Run Miri on at least a representative subset, or explain why it is skipped.

### P1: Analysis Soundness and Rejection Quality

- Strengthen pointer role classification beyond regex evidence.
- Add clearer aliasing evidence and reasons for manual-refactor decisions.
- Improve macro/preprocessor reporting.
- Track external calls and library dependencies more precisely.
- Separate "unsupported by Rust safe subset" from "unsupported by current
  prototype implementation" in reports.
- Add tests for false positives and false negatives in eligibility
  classification.

### P1: Safe Synthesis Coverage

- Expand deterministic synthesis for manual allocation patterns.
- Add additional allocation initialization shapes beyond the current simple
  `Box<T>` and `Vec<T>` cases.
- Add support for simple struct-return and struct-field access idioms.
- Add safe translations for more string-processing cases.
- Add selected loop reductions beyond sum/max.
- Improve generated Rust naming, formatting, and API consistency.

## Medium-Priority Engineering TODOs

### P2: Reporting and Metrics

- [x] Add a single canonical result schema version to each CSV/JSON artifact.
- [x] Include report-generation timestamp and git commit hash when available.
- [x] Make combined evaluation reject mismatched denominators unless explicitly
  configured.
- [x] Add markdown and LaTeX export parity tests.
- [x] Track skipped, unsupported, failed, and not-applicable validation
  separately.
- [x] Add a command that prints a publication-ready metric summary from
  canonical CSV inputs.

### P2: CLI and Configuration

- [x] Make benchmark modes explicit in the README and CLI help.
- [x] Add examples for running only `safemap_full`, only `c2rust_only`, and the
  LLM subset.
- [x] Warn when an LLM config has no usable API key before starting a long run.
- [x] Add a dry-run mode that validates external tool availability.
- [x] Clarify output directory behavior so reruns do not mix fresh and stale
  artifacts.

### P2: Test Coverage

- Keep the unit suite green as the primary regression gate.
- [x] Add integration tests for full final-eval artifact generation.
- [x] Add integration tests for combined-eval denominator consistency.
- [x] Add integration tests for expected unsupported examples.
- [x] Add integration tests for LLM failure classification with a static fake
  client.
- [x] Add integration tests for generated LaTeX table fragment consistency.
- [x] Add tests that publication snapshots reject incomplete or unexpected
  artifact sets.
- Add tests for multi-file project ingestion and compile database recovery.

### P2: Documentation

- [x] Update `README.md` after paper-number reconciliation.
- [x] Update `SAFEMAP_CODEX_SOURCE_OF_TRUTH.md` after paper-number
  reconciliation.
- [x] Add a concise "How to reproduce paper tables" section.
- Add a "Known limitations" section that mirrors the paper's threats to
  validity.
- Link the paper draft path and artifact-generation commands from the research
  TODO or README.

## Longer-Term TODOs

### P3: Project-Scale Migration

- Improve multi-file dependency graphs and translation-unit grouping.
- Add support for internal helper functions and call graphs in synthesis.
- Handle headers and shared structs more robustly.
- Add partial migration output that clearly separates accepted safe units from
  manual-refactor units.

### P3: Stronger Semantics

- Use AST/CFG information more deeply instead of regex-heavy synthesis.
- Add loop invariant and bounds evidence for more pointer-to-slice rewrites.
- Add ownership/lifetime evidence for borrow choices.
- Explore translation validation or formal methods for small supported subsets.

### P3: Artifact Packaging

- Package raw inputs, generated outputs, reports, and scripts for archival.
- Add Docker or devcontainer support if external tools can be pinned reliably.
- [x] Add a CI job for unit tests and Python compilation.
- Add a lightweight benchmark smoke test to CI.
- Add optional long-running evaluation jobs outside normal CI.

## Current Publication Readiness

### Ready Now

- Start writing the paper.
- Present the safe-first architecture.
- Present strict acceptance as the central contribution.
- Present deterministic SafeMAP results on the existing microbenchmarks and
  case studies.
- Present C2Rust as a strict-policy baseline after denominator reconciliation.
- Present unsupported constructs as explicit rejection behavior.

### Not Ready Yet

- Submit to a strong systems/software-engineering venue without more evaluation.
- Claim broad C coverage or real-world project migration.
- Claim strong external generalization: deterministic synthesis accepted only
  `1 / 22` eligible units in the pinned LLVM external corpus.
- Claim LLM effectiveness from the current Gemini/Ollama subset.
- Claim formal equivalence from current differential tests.
- Claim Miri-backed validation if evaluated rows skipped Miri.

### Best Near-Term Submission Target

The project is closest to a workshop paper, short paper, artifact paper, or
prototype/tool-demo submission. A stronger conference/journal submission needs
a larger and less hand-curated benchmark set, a cleaner reproducibility story,
and reconciled paper tables.

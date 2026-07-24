# SafeMAP Paper Review

Reviewed: 2026-07-23

Scope: `/mnt/data/college/research/my_paper/main.tex`, its four generated table
fragments, bibliography, reference inventory, the canonical publication
artifacts, and the new outcome-blind LLVM external-corpus result.

This report records the review that guided the 2026-07-23 revision. The
line-number references below describe the pre-revision draft and are retained
as an audit trail.

## Resolution status

The revision resolves the paper-content issues identified below:

- separates analyzer eligibility, implemented synthesis support, and policy
  acceptance;
- reports the outcome-blind LLVM corpus separately, with its pinned source,
  selection rule, hashes, license records, corpus statistics, and `1 / 22`
  acceptance result;
- states that the external accepted helper has no behavioral test or applicable
  differential check;
- reports the current `111`-test repository validation pass and zero LLM calls
  in the canonical deterministic runs;
- corrects the C2Rust denominator explanation and the distinction between
  target and unit counts;
- removes the unpublished LLM row from the primary result table;
- narrows the claims, updates the methodology and threats to validity, and adds
  the LLVM test-suite citation.

The rebuilt five-page PDF has no LaTeX errors, undefined citations/references,
or overfull boxes. Four underfull-box spacing warnings remain. Submission still
requires real author metadata and the planned publisher/DOI metadata audit.
The publication and external snapshots were regenerated from clean commit
`ac1d92c` on 2026-07-23. Behavioral integration with LLVM reference outputs
remains future evaluation work.

## Verdict

The revised draft has a clear central idea and is suitable as the basis of a
workshop or tool-demo paper. It now presents the gap between SafeMAP's
eligibility classification and implemented synthesis coverage as a result and
limitation instead of combining unlike datasets. The remaining submission
items are listed in the resolution status above.

## Must fix before submission

### 1. Define eligibility independently from synthesis support

Lines 89--90, 197--208, and 285--290 present the eligible-unit denominator as
the restricted subset SafeMAP can translate. On the pinned LLVM corpus, however,
the analyzer marks 22 units eligible while deterministic synthesis accepts only
one. Nine of ten projects produce no supported deterministic output.

The paper should distinguish at least:

- `safe_eligible_in_principle`: the analyzer did not find a construct that
  inherently requires unsafe Rust or manual refactoring;
- `implemented_synthesis_support`: the current synthesizer has a matching,
  implemented source pattern;
- `policy_accepted`: generated Rust passed the final-output policy.

Without this distinction, a reader cannot tell whether `1/22` measures hard
translation failures, incomplete pattern implementation, or false-positive
eligibility.

### 2. Add the external corpus as a separately labeled result

The dataset section at lines 274--283 describes only authored inputs, and the
future-work paragraph at lines 402--403 still says corpus expansion is the next
step. Add a separate external-corpus subsection with:

- source: LLVM test-suite `SingleSource/Benchmarks/Misc`;
- pinned commit: `6cdc54e005552e3444fa7402cd18a6e4b6db195d`;
- outcome-blind rule: matching reference output, no more than 100 physical
  source lines, and no architecture-gated source;
- all ten selected programs, with no result-based exclusions;
- license and source-hash preservation;
- 589 C LOC, 32 functions, 45 parameters, 11 pointer parameters, approximate
  aggregate cyclomatic complexity 93, and three detected unsupported
  constructs;
- deterministic result: 1 accepted unit out of 22 eligible units (`0.045`);
- nine rows with `no_supported_synthesis`.

Do not merge this rate with the authored microbenchmark or case-study rate.
The source population, selection process, mode, and validation coverage differ.

### 3. Do not imply behavioral validation for the external accepted unit

The accepted `mandel_2` unit passed Cargo check, Cargo test, Clippy, and the
no-unsafe/no-public-raw-pointer checks. Differential validation was
`not_applicable`; the current generic harness does not consume LLVM's retained
reference output. The accepted output contains only the scalar helper `sqr`,
and Cargo test passed with no behavioral test cases.

Lines 32--34 and 197--208 are defensible only because they say “available”
behavioral validation. When reporting the external result, state explicitly
that acceptance is policy acceptance with differential validation unavailable.
Avoid describing it as behaviorally equivalent.

The acceptance policy currently treats `passed`, `skipped`, and
`not_applicable` differential statuses as non-rejecting. Only `passed` is now
counted in the `differential_pass_units` metric. This policy should be explicit
in the methodology and tables.

### 4. Correct stale and incomplete execution details

- Line 294 says `99` tests. The repository now collects and passes `111`.
- The new external artifacts are under `reports/external-corpus/` but are not
  yet part of the canonical `reports/publication/` reproduction snapshot.
- Existing canonical manifests record `git_dirty: true` and identify commit
  `28a161e...`, not the commit that contains the snapshot.
- The paper should state that `safemap_full` made zero LLM calls in the
  canonical microbenchmark and case-study CSVs. Otherwise “full” can be read as
  an LLM-assisted result even though the reported accepted output was
  deterministic.

### 5. Fix the C2Rust denominator framing

Lines 39--41 say C2Rust accepts zero units “because” two rows lacked complete
metrics. The missing rows explain the denominator of 72 rather than 76; they do
not explain why the accepted count is zero.

Prefer an intention-to-translate comparison that retains failed rows as failed
outcomes, or report:

- the matched-row denominator;
- the two infrastructure/metric failures separately;
- `0` policy-accepted raw C2Rust units in either interpretation.

The current denominator override is transparent in the artifact, but unequal
denominators weaken the table as a direct comparison.

### 6. Explain target counts versus unit counts

Lines 309--312 give both `37/76` accepted units and `36/40` accepted declared
targets but do not explain the difference. Add a concrete definition of unit
formation and state which non-target/helper or entry-point unit accounts for
the extra accepted unit. Do the same for the case studies, where each project
has three declared targets but four eligible units.

### 7. Either publish or remove the LLM row from the main result table

The table reports the bounded LLM subset, but the canonical reproduction
manifest says `llm_csv_included: false`. The draft correctly warns against
generalizing the result, but a main results row should still have published
prompts, responses, provider/model configuration, token counts, and failure
reasons.

Until those artifacts are included, move the LLM result to an engineering
observations paragraph or remove it from the primary evaluation table.

## Important improvements

### Strengthen the methodology

Add operational detail for:

- libclang versus regex-fallback analysis and which path generated each result;
- translation-unit construction and dependency grouping;
- how eligibility categories map to the eligible denominator;
- deterministic pattern matching and what causes `no_supported_synthesis`;
- project-level validation being attributed to function/planned units;
- exact commands, hardware, timeouts, and tool versions, with a pointer to the
  manifest rather than only the artifact directory.

### Reframe the contribution claim

The external result supports a narrower and more interesting claim:

> A strict safe-first policy makes unsupported synthesis coverage visible; on
> independently authored small C programs, current eligibility analysis is much
> broader than deterministic synthesis coverage.

That claim is stronger than presenting high acceptance on authored idiom
examples, because it demonstrates the audit value of rejection while being
honest about prototype maturity.

### Improve baseline positioning

A raw C2Rust strict-policy baseline predictably scores zero because its purpose
is semantic preservation through unsafe/raw-pointer Rust. Present it as a policy
calibration or lower bound, not the only competitive effectiveness baseline.
The paper would benefit from either a post-C2Rust safety-rewrite baseline or a
carefully bounded comparison to a related safe-translation tool.

### Update threats to validity

Lines 374--377 should now say that external authorship bias is partly reduced,
while retaining these limitations:

- one upstream directory;
- ten programs;
- an outcome-blind but size-capped selection;
- compiler/numerical benchmark programs rather than deployed applications;
- no use yet of upstream reference outputs;
- old C dialects and compiler extensions in some sources.

### Tighten terminology

Use “policy-accepted fully safe Rust” when semantic equivalence has not been
established. “Fully safe” accurately describes the Rust safety policy, but can
otherwise be misread as a broader correctness guarantee.

## Editorial and artifact notes

- Replace the author, affiliation, and email placeholders at lines 16--19.
- Add citations for the LLVM test-suite guide/repository and the pinned corpus
  commit.
- The C2Rust bibliography entry should cite the evaluated release (`0.22.1`)
  and an access date or immutable release URL rather than only year `2026`.
- The reference inventory still says publisher metadata must be verified.
  Several entries were derived from local PDFs; complete a DOI/publisher audit
  before submission.
- The existing PDF log has no fatal, undefined-reference, or overfull-box
  messages, but it has multiple underfull-box warnings. The PDF predates the
  external-corpus result and must be rebuilt after revision.
- Break long table prose, especially the baseline table, into shorter cells or
  move interpretation into body text.

## Recommended revised evaluation structure

1. Authored idiom microbenchmarks: characterize supported-pattern behavior.
2. Authored module-shaped cases: characterize composition.
3. Outcome-blind LLVM subset: characterize external generalization and
   eligibility/synthesis mismatch.
4. C2Rust strict-policy calibration: show what raw baseline output does not
   satisfy.
5. Optional LLM engineering study: include only when its artifacts are
   published and reproducible.

This structure answers the current RQs without implying project-scale or broad
C coverage.

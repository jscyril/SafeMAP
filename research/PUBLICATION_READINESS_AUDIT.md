# SafeMAP Publication-Readiness and Originality Audit

Audit date: 2026-07-28

## Verdict

The manuscript is now a coherent pre-evaluation conference draft, but it is
not yet ready to submit. The technical mechanism, development evidence,
validation policy, evaluation protocol, and threats to validity are
substantive. The blocking issue is empirical: the sealed held-out experiment,
independent eligibility labels, and competitive baseline have not yet produced
results.

No held-out result was invented or inferred from development data. The paper
now says this explicitly.

## Changes made in this publication pass

- Rewrote the abstract to distinguish completed development evidence from the
  unexecuted held-out study.
- Removed claims that the evaluation was “preregistered”; the protocol is
  described as pre-specified and frozen instead.
- Replaced draft/submission-gate language with a precise held-out evaluation
  status section.
- Corrected the development denominator: the full microbenchmark configuration
  validates 36/81 total units, including 36/76 candidate-safe units.
- Added an outcome-cascade table and a component-ablation table.
- Updated future work so it no longer lists fixed arrays, scalar structs,
  internal calls, simple entry-point composition, or multi-function crates as
  unimplemented.
- Tightened the discussion and conclusion so they do not imply held-out
  effectiveness.
- Added an anonymous-submission author toggle.
- Added primary citations for AddressSanitizer and UBSan.
- Rechecked the bibliography against Crossref and publisher records.

## Bibliography corrections

The audit found and corrected the following metadata:

| Reference | Correction |
|---|---|
| Hong, ICSE Companion 2023 | pages 273–277 |
| Hong and Ryu, EMSE | volume 30, issue 1, article 3 |
| C2SaferRust, TSE | pages 618–630 |
| Scylla, PACMPL | pages 823–849 |
| C2RustTV, COMPSAC | pages 1254–1259 |
| RustMap, ICECCS | pages 283–302 and DOI added |
| Valenzuela et al. | publication year 2025 |
| Viirola et al. | publication year 2025 |
| RustFlow | issue 1 added |
| In Rust We Trust | corrected IEEE DOI |
| C2Rust repository | changed from a misleading publication year to an access date |

Records were checked through the corresponding DOI metadata and, where
available, the publisher or project page. Useful primary records include:

- AddressSanitizer: https://www.usenix.org/conference/atc12/technical-sessions/presentation/serebryany
- UBSan: https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
- C2Rust: https://github.com/immunant/c2rust
- LLVM test-suite guide: https://llvm.org/docs/TestSuiteGuide.html
- Flourine: https://arxiv.org/abs/2405.11514

## Originality and plagiarism check

This was a source-level audit, not an iThenticate or Turnitin similarity report.
Eight distinctive sentences from the abstract, mechanism, results, and
conclusion were searched as exact phrases. No matching publication or webpage
was found. This lowers the risk of obvious verbatim copying but is not proof of
originality: web search does not cover subscription databases, unpublished
work, or every indexed document.

The related-work section paraphrases cited papers and does not contain long
quotations. Technical names, benchmark names, taxonomy labels, and standard
validation terminology will naturally match other documents and should be
reviewed rather than mechanically removed from a similarity report.

Before submission:

1. Run the final PDF through the institution’s licensed iThenticate or Turnitin
   account.
2. Inspect every highlighted passage manually. A total percentage alone is not
   a plagiarism finding.
3. Verify that each technical claim about prior work is supported by the cited
   source.
4. Quote any borrowed wording explicitly, although the current paper does not
   appear to need direct quotations.
5. Retain the similarity report and the revision made in response to it.

## AI-authorship check

There is no reliable source-level test that can establish whether prose was
written or edited by an LLM. AI detectors return probabilistic classifications
and can produce both false positives and false negatives, especially for
technical prose and human/AI-edited text. Turnitin’s own current guidance
withholds low-range scores and highlights to reduce false-positive
interpretation.

The manuscript was therefore audited for the risks that matter to publication:

- unsupported or fabricated claims;
- fabricated citations;
- generic prose that obscures the contribution;
- repeated formulaic transitions;
- inconsistent terminology;
- development results presented as independent evidence.

Those issues were corrected where found. The remaining prose is technically
specific and traceable to the implementation artifacts. This does not replace
the venue’s AI-use policy. Because an AI system materially edited this draft,
the authors should retain an edit log and disclose the assistance if the target
venue requires disclosure. Do not rewrite solely to evade an AI detector.

## Submission blockers

1. **Run the held-out study once after freeze.** Replace the held-out status
   paragraph with generated corpus, eligibility, outcome-cascade, role,
   module, baseline, and ablation tables.
2. **Complete two outcome-blind eligibility reviews.** Report raw agreement,
   Cohen’s kappa, adjudication, false positives, false negatives, construct
   disagreements, and backend provenance.
3. **Freeze the competitive baseline.** Replace
   `REPLACE_WITH_FROZEN_BASELINE_MODEL` in
   `research/conference_evaluation.yaml` with the exact model identifier and
   freeze the remaining sampling settings.
4. **Run both comparison lanes.** Direct C-to-safe-Rust LLM and raw C2Rust must
   face the same policy and behavioral gates.
5. **Select the venue.** Confirm template, page limit, anonymity policy,
   artifact rules, and AI-use disclosure policy.
6. **Complete authorship metadata.** The current source builds as an anonymous
   submission. Add names, affiliations, ORCIDs if requested, and email
   addresses for a non-anonymous or camera-ready version.
7. **Perform an author fact check.** An author must inspect every result table,
   source revision, citation, and claim against the retained artifact.
8. **Archive the artifact.** Pin dependencies and toolchains, add a reproduction
   entry point, and preferably archive the evaluated revision with a DOI.

## Verification performed

- Repository tests: 144 tests passed.
- LaTeX: clean six-page PDF build.
- Cross-references and citations: resolved.
- Overfull boxes: none reported.
- Held-out corpus: not opened or executed during this audit.


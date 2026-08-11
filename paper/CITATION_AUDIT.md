# Citation and reference audit

Checked: 11 August 2026

## Mechanical checks

- Citation keys used in `main.tex`: **20**
- Bibliography records in `references.bib`: **20**
- Missing cited records: **0**
- Unused bibliography records: **0**
- Undefined citations in the final LaTeX build: **0**
- Bibliography records with DOI: **15**
- Records using an official project/publisher page or arXiv identifier: **5**

All 15 DOI routes resolved to their publisher landing route during the check.
Some ACM landing pages denied automated page retrieval after the DOI redirect;
that is recorded as an access restriction, not treated as a missing reference.
The remaining records were checked against arXiv, the official C2Rust
repository, LLVM documentation, or the USENIX publication page.

## Claim-to-source review

| Manuscript topic | Keys checked | Result |
|---|---|---|
| Raw C2Rust as a behavior-preserving, commonly unsafe starting point | `c2rust`, `emre2021safer`, `hong2023static` | The cited sources match the scoped claim. |
| Static analysis, ownership, and safer transpiler designs | `ling2022trust`, `zhang2023ownership`, `mohapatra2026cp2srust`, `nitin2026c2saferrust` | Titles, venues, and DOI records support the related-work summary. |
| Direct/LLM-assisted C-to-Rust translation and validation | `hong2025typemigrating`, `zhou2025c2rusttv`, `eniser2025fluorine`, `valenzuela2026llmcompile`, `zhang2026rustflow`, `cai2025rustmap` | Each citation is used for its stated translation, repair, testing, or project-scale focus. |
| Translation of a structured C subset to safe Rust | `fromherz2026scylla` | Scope matches the manuscript wording. |
| Migration feasibility and industry context | `hong2025cacm`, `viirola2026feasible` | The paper uses these sources only for high-level feasibility/manual-work context. |
| Undefined-behavior detection | `jung2026miri`, `serebryany2012asan`, `clangubsan` | The manuscript distinguishes Miri, ASan, and UBSan and does not count skipped Miri as a pass. |
| LLVM development-corpus provenance | `llvmtestsuite` | The official guide URL and exact pinned commit are recorded. |

## Items for the eventual venue check

- Bibliography keys containing a different year than the rendered record
  (`valenzuela2026llmcompile` and `viirola2026feasible`) are internal identifiers;
  the displayed records correctly use 2025. Renaming them is optional and would
  not change the citation.
- Recheck access dates immediately before submission if the venue requires a
  specific date style.
- Confirm whether the venue permits arXiv-only citation for
  `eniser2025fluorine` or requires a later archival version if one appears.
- Do not add Google model documentation to the scholarly bibliography unless
  the held-out baseline is reported in the manuscript; the exact official URLs
  and access basis are already frozen in the evaluation protocol.

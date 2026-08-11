# Similarity and AI-report review checklist

The institutional reports are screening signals, not verdicts. Review every
flag in context and keep the original report with the reviewed final draft.

## Before upload

- [ ] Upload only the canonical `paper/main.pdf`, not source ZIPs, old PDFs,
      reviewer packets, or generated-code appendices unless requested.
- [ ] Confirm the PDF opens, text is selectable, fonts are embedded, figures
      are legible, and no comments or hidden draft text remain.
- [ ] Record the PDF SHA-256, page count, build time, Git commit, and checker
      settings/exclusions.
- [ ] If permitted, exclude the bibliography, quoted material, and small
      matches consistently; record rather than conceal those settings.

## Similarity report

- [ ] Inspect each substantial match, not only the aggregate percentage.
- [ ] Mark properly quoted and cited text, bibliography entries, standard
      terminology, template boilerplate, and unavoidable method names.
- [ ] For uncited close wording, either quote it within venue limits or rewrite
      from the authors' own understanding and add the correct citation.
- [ ] Check self-overlap with theses, proposals, reports, preprints, repository
      README files, and earlier manuscript versions.
- [ ] Look for patchwriting: small synonym changes that retain another source's
      sentence structure. Rewrite the idea genuinely and cite it.
- [ ] Do not weaken technical precision, remove citations, manipulate Unicode,
      insert hidden text, or make cosmetic edits solely to reduce the score.
- [ ] Record each material flag, decision, source, and edit in a private review
      log; rebuild and hash the corrected PDF.

## AI-content report

- [ ] Treat the detector score as uncertain. Do not claim that it proves human
      or AI authorship.
- [ ] Read every highlighted passage for factual accuracy, vague attribution,
      fabricated detail, repetition, generic transitions, and unsupported
      confidence.
- [ ] Verify every citation and numerical claim against the cited source or
      frozen artifact, regardless of whether the passage was flagged.
- [ ] Revise only when the prose or evidence is genuinely weak. Preserve clear,
      accurate writing even if a detector dislikes its style.
- [ ] Follow the university and venue disclosure rules for any generative-AI
      assistance. Keep author responsibility for all claims explicit.

## Final control

- [ ] All authors approve the post-report changes.
- [ ] The rebuilt PDF is visually inspected again.
- [ ] The submitted SHA-256 matches the approved canonical PDF.
- [ ] Archive the submitted PDF, reports, review log, and submission receipt in
      a private location with access appropriate to university policy.

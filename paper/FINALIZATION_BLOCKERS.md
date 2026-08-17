# Final-draft blockers

The automatic frozen experiment is complete. The canonical PDF is not ready
for institutional submission until every item below is resolved.

## Human review

- [x] Obtain the research guide's approval for reviewer ethics, consent, and
      disclosed relationship/conflict handling.
- [x] Recruit and screen two reviewers privately and send both the unchanged
      `ui2` packet.
- [x] Receive and hash both independent CSV and JSON exports before either
      response is shared or adjudication begins.
- [x] Run the merge/validation and consensus-only workflow, retain 27
      disagreements as unresolved, regenerate statistics, and replace the
      manuscript's pending statement.
- [x] Obtain research-guide approval for omitting planned adjudication and for
      reporting consensus-only metrics as a disclosed protocol deviation.

## Authors and venue

- [x] Confirm each author's name, order, role, and `Bangalore` city spelling.
- [ ] Confirm each author's official department, institution, and country.
- [x] Replace both remaining `email address or ORCID` placeholders.
- [ ] Obtain explicit manuscript approval from the research guide and RAC
      member.
- [ ] Fill in venue, category, anonymity, page-limit, paper-size, declaration,
      and generative-AI disclosure requirements in `SUBMISSION_METADATA.md`.
- [x] Rebuild and re-check the bibliography balancing trigger after edits.

## Institutional checker and submission

- [x] Rebuild and visually inspect the plagiarism-check draft PDF after
      human-review and author changes.
- [x] Record the plagiarism-check draft SHA-256, page count, build time, and
      source commit in `PLAGIARISM_CHECK_DRAFT.md`.
- [ ] Verify that the institutional upload is exactly `paper/main.pdf` with the
      recorded SHA-256.
- [ ] Review similarity and AI-content flags using
      `SIMILARITY_AI_REPORT_REVIEW.md`; do not edit merely to chase a score.
- [ ] Obtain all authors' approval for any post-report changes and archive the
      final PDF, reports, and receipt privately.

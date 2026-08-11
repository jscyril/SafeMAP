# Canonical SafeMAP paper

This is the only manuscript source directory used for the final-draft PDF.
The older `/mnt/data/college/research/my_paper` directory is retained as source
history and must not be edited or submitted.

Generated result tables belong in `tables/` and must come from the frozen CSV
and JSON artifacts. Do not hand-edit numerical results in a generated table.

Build from this directory with:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The canonical submission artifact is `main.pdf`. Before sending it to the
research guide, complete `AUTHOR_FACT_CHECK.md`, `SUBMISSION_METADATA.md`, and
`SIMILARITY_AI_REPORT_REVIEW.md`, then rebuild and visually inspect every page.

The held-out outcome branch must remain private or unpushed until both human
reviewers have returned frozen responses. Reviewer packets must not contain or
link to SafeMAP outcomes.

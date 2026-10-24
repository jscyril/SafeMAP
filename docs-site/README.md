# SafeMAP Documentation Site

This directory contains a static book-style documentation website for SafeMAP.

Open `index.html` directly in a browser:

```bash
xdg-open docs-site/index.html
```

or serve it locally:

```bash
python -m http.server 8000 --directory docs-site
```

Then visit:

```text
http://localhost:8000
```

No build step is required.

Current documentation snapshot (v2 evaluation, with amendment 3):

- test suite: `179 passed`
- held-out corpus: `10` C libraries, `356` translation units, sealed protocol
- SafeMAP (guided): `36-37 / 356` accepted units across three runs (sealed: `12-16`)
- one-shot LLM given the planned interfaces: `28-31`; plain LLM: `1-2`; raw C2Rust: `0`
- acceptance check: `92.7%` of non-equivalent compiling mutants rejected
- table generation: `python3 scripts/generate_v2_manuscript_tables.py reports/publication/v2/heldout reports/publication/v2/development out/`
- replication package: https://doi.org/10.5281/zenodo.23619725

When results change, update the numbers in `index.html` (hero tiles and the
Evaluation Results section) and here together.

## GitHub Pages

This directory is ready for GitHub Pages. The repository includes:

```text
.github/workflows/pages.yml
docs-site/.nojekyll
```

After pushing to GitHub:

1. Open the repository settings.
2. Go to **Pages**.
3. Set **Source** to **GitHub Actions**.
4. Push to `main` or manually run the **Deploy Docs Site** workflow.

The workflow publishes the contents of `docs-site` as the Pages site.

## Troubleshooting

If deployment fails with `Multiple artifacts named "github-pages"`, rerun after
this workflow change is pushed. The workflow uses an explicit artifact name,
`safemap-docs-pages`, so `actions/deploy-pages` does not collide with another
default Pages artifact created in the same run.

Node deprecation warnings from GitHub-hosted actions are not the deployment
failure in that case; the duplicate Pages artifact is.

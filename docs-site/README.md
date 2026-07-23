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

Current documentation snapshot:

- test suite: `102 passed`
- benchmark examples: `40`
- SafeMAP-only final eval: `37 / 76` accepted eligible units
- case studies: `5` modules, `15 / 20` accepted eligible units
- C2Rust baseline: `0 / 72` accepted eligible units in the canonical snapshot
- paper-table workflow: `make paper-artifacts`
- preflight workflow: `python -m safemap.cli final-eval --benchmarks examples --output reports/final --mode safemap_full --dry-run`

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

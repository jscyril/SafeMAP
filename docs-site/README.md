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

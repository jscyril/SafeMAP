# Contributing to SafeMAP

SafeMAP is a research prototype. Contributions should preserve the safe-first
framing: C2Rust is a baseline/reference lane, and SafeMAP success means fully
safe accepted Rust, not just fewer unsafe blocks.

## Local Validation

Run before opening a pull request:

```bash
pytest -q
python -m compileall -q safemap tests
```

For benchmark/reporting changes, also run:

```bash
python -m safemap.cli final-eval \
  --benchmarks examples \
  --output reports/final \
  --mode safemap_full \
  --dry-run

python -m safemap.cli final-eval \
  --benchmarks examples \
  --output reports/final \
  --mode safemap_full
```

## Safety Rules

Accepted SafeMAP output must:

- compile with `#![forbid(unsafe_code)]`;
- contain no `unsafe`, `unsafe fn`, or `unsafe impl`;
- expose no raw-pointer public API;
- pass available validation;
- keep unsupported C constructs reported instead of forced through unsafe output.

## Do Not Commit

- real API keys;
- `.env` files;
- generated `.safemap/`, `results/`, `work/`, or `reports/final/` run outputs;
- Cargo `target/` directories;
- Python caches or virtual environments.

Use `.env.example`, `safemap.gemini.yaml`, and `safemap.ollama.yaml` as
templates only.

## Documentation

When changing behavior, update:

- `README.md`;
- `SAFEMAP_RESEARCH_TODO.md`;
- `SAFEMAP_CODEX_SOURCE_OF_TRUTH.md` if the research framing changes;
- `docs-site/index.html` if user-facing commands, examples, or metrics change.

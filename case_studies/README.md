# SafeMAP Case Studies

This directory contains authored case-study modules for paper evaluation.

The modules are not copied from third-party projects. They are small,
reproducible C utilities modeled after common real-world C patterns:
configuration readers, buffer metrics, string record helpers, scalar output
helpers, and allocation factories.

Use them separately from the microbenchmark suite:

```bash
python -m safemap.cli final-eval \
  --benchmarks case_studies \
  --output reports/case-studies \
  --mode safemap_full
```

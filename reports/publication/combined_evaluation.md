# SafeMAP Combined Evaluation Summary

## Evaluation Overview

| Dataset | Mode | Rows | Accepted Units | Eligible Units | Acceptance Rate | Differential Passed | Accepted Target Functions | Target Functions | Target Function Rate | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Microbenchmarks | safemap_full | 40 | 37 | 76 | 0.487 | 37 | 36 | 40 | 0.900 | SafeMAP fully safe output |
| Case studies | safemap_full | 5 | 15 | 20 | 0.750 | 5 | 15 | 15 | 1.000 | Authored module-shaped case studies |
| C2Rust baseline | c2rust_only | 40 | 0 | 72 | 0.000 | 0 | 0 | 40 | 0.000 | Strict SafeMAP acceptance applied to raw C2Rust baseline |

## Dataset Characterization

| Dataset | Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Microbenchmarks | safemap_full | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Case studies | safemap_full | 129 | 20 | 12 | 21 | 0.571 | 28 | 0 |
| C2Rust baseline | c2rust_only | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |

## Interpretation

- Accepted units are counted only when the final Rust output satisfies SafeMAP's fully safe policy.
- C2Rust baseline rows are not treated as SafeMAP success unless they satisfy the same no-unsafe/no-raw-pointer policy.
- LLM subset results are latency/model dependent and should not be generalized to the full benchmark suite.
- Unsupported C constructs are reported as explicit outcomes rather than crashes.

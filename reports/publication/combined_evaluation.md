# SafeMAP Combined Evaluation Summary

## Evaluation Overview

| Dataset | Mode | Rows | Accepted Units | Eligible Units | Acceptance Rate | Differential Passed | Accepted Target Functions | Target Functions | Target Function Rate | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Microbenchmarks | safemap_deterministic | 40 | 37 | 76 | 0.487 | 36 | 36 | 40 | 0.900 | SafeMAP fully safe output |
| Case studies | safemap_deterministic | 5 | 15 | 20 | 0.750 | 5 | 15 | 15 | 1.000 | Authored module-shaped case studies |
| LLVM external corpus | safemap_deterministic | 10 | 1 | 22 | 0.045 | 1 | 0 | 0 | 0.000 | Outcome-blind pinned LLVM subset with reference-output validation |
| C2Rust baseline | c2rust_only | 40 | 0 | 76 | 0.000 | 0 | 0 | 40 | 0.000 | Strict SafeMAP acceptance applied to raw C2Rust baseline |
| Static-guidance ablation | safemap_no_static_guidance | 40 | 0 | 76 | 0.000 | 0 | 0 | 40 | 0.000 | Structured analysis and migration plans withheld from synthesis |

## Dataset Characterization

| Dataset | Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Microbenchmarks | safemap_deterministic | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Case studies | safemap_deterministic | 129 | 20 | 12 | 21 | 0.571 | 28 | 0 |
| LLVM external corpus | safemap_deterministic | 589 | 32 | 11 | 45 | 0.244 | 93 | 3 |
| C2Rust baseline | c2rust_only | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Static-guidance ablation | safemap_no_static_guidance | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |

## Interpretation

- Accepted units are counted only when the final Rust output satisfies SafeMAP's fully safe policy.
- C2Rust baseline rows are not treated as SafeMAP success unless they satisfy the same no-unsafe/no-raw-pointer policy.
- The no-static-guidance ablation still runs analysis to preserve the evaluation denominator, but withholds its classifications, signatures, and migration plans from synthesis.
- Unsupported C constructs are reported as explicit outcomes rather than crashes.

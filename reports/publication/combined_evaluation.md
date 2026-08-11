# SafeMAP Combined Evaluation Summary

## Evaluation Overview

| Dataset | Mode | Rows | Accepted Units | Eligible Units | Acceptance Rate | Differential Passed | Accepted Target Functions | Target Functions | Target Function Rate | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Microbenchmarks | safemap_deterministic | 40 | 36 | 76 | 0.474 | 36 | 35 | 40 | 0.875 | SafeMAP fully safe output |
| Case studies | safemap_deterministic | 6 | 17 | 25 | 0.680 | 5 | 17 | 20 | 0.850 | Authored module-shaped case studies |
| LLVM external corpus | safemap_deterministic | 10 | 6 | 21 | 0.286 | 4 | 0 | 0 | 0.000 | Outcome-blind pinned LLVM subset with reference-output validation |
| C2Rust baseline | c2rust_only | 40 | 0 | 76 | 0.000 | 0 | 0 | 40 | 0.000 | Strict SafeMAP acceptance applied to raw C2Rust baseline |
| Static-guidance ablation | safemap_deterministic | 40 | 36 | 76 | 0.474 | 36 | 35 | 40 | 0.875 | Structured analysis and migration plans withheld from synthesis |
| Static-guidance ablation | safemap_without_dependency_grouping | 40 | 36 | 76 | 0.474 | 36 | 35 | 40 | 0.875 | Structured analysis and migration plans withheld from synthesis |
| Static-guidance ablation | safemap_without_idiom_plans | 40 | 6 | 76 | 0.079 | 6 | 5 | 40 | 0.125 | Structured analysis and migration plans withheld from synthesis |
| Static-guidance ablation | safemap_without_pointer_roles | 40 | 16 | 73 | 0.219 | 16 | 15 | 40 | 0.375 | Structured analysis and migration plans withheld from synthesis |
| Static-guidance ablation | safemap_without_safe_signatures | 40 | 6 | 76 | 0.079 | 6 | 5 | 40 | 0.125 | Structured analysis and migration plans withheld from synthesis |
| Static-guidance ablation | safemap_without_validation_feedback | 40 | 36 | 76 | 0.474 | 36 | 35 | 40 | 0.875 | Structured analysis and migration plans withheld from synthesis |

## Dataset Characterization

| Dataset | Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Microbenchmarks | safemap_deterministic | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Case studies | safemap_deterministic | 157 | 25 | 14 | 25 | 0.560 | 34 | 0 |
| LLVM external corpus | safemap_deterministic | 589 | 32 | 20 | 45 | 0.444 | 93 | 3 |
| C2Rust baseline | c2rust_only | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Static-guidance ablation | safemap_deterministic | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Static-guidance ablation | safemap_without_dependency_grouping | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Static-guidance ablation | safemap_without_idiom_plans | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Static-guidance ablation | safemap_without_pointer_roles | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Static-guidance ablation | safemap_without_safe_signatures | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| Static-guidance ablation | safemap_without_validation_feedback | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |

## Interpretation

- Accepted units are counted only when the final Rust output satisfies SafeMAP's fully safe policy.
- C2Rust baseline rows are not treated as SafeMAP success unless they satisfy the same no-unsafe/no-raw-pointer policy.
- The no-static-guidance ablation still runs analysis to preserve the evaluation denominator, but withholds its classifications, signatures, and migration plans from synthesis.
- Unsupported C constructs are reported as explicit outcomes rather than crashes.

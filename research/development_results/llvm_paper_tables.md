# SafeMAP Paper Tables

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| safemap_deterministic | 10 | `completed`: 4, `no_supported_synthesis`: 6 | 6 | 23 | 0.261 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|

## Idiom Success

| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |
|---|---|---:|---:|---:|
| safemap_deterministic | boolean_int | 1 | 0 | 0.000 |
| safemap_deterministic | pointer_length_array | 2 | 1 | 0.500 |

## Failure Categories

| Mode | Category | Count |
|---|---|---:|
| safemap_deterministic | requires_manual_refactor | 5 |
| safemap_deterministic | unsafe_required | 1 |
| safemap_deterministic | unsupported | 3 |

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|
| safemap_deterministic | c_sanitizers | passed | 4 |
| safemap_deterministic | cargo_check | passed | 4 |
| safemap_deterministic | cargo_test | passed | 4 |
| safemap_deterministic | clippy | passed | 4 |
| safemap_deterministic | differential | passed | 4 |
| safemap_deterministic | miri | skipped | 4 |

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| safemap_deterministic | 589 | 32 | 11 | 45 | 0.244 | 93 | 3 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| dt | safemap_deterministic | 51 | 2 | 0.5 | 8 | 0 | 0 | 0.0 |  |  |
| fp_convert | safemap_deterministic | 45 | 2 | 0.4 | 6 | 0 | 1 | 0.5 | passed | skipped |
| lowercase | safemap_deterministic | 58 | 4 | 0.429 | 13 | 0 | 0 | 0.0 |  |  |
| mandel | safemap_deterministic | 48 | 3 | 0.0 | 7 | 1 | 0 | 0.0 |  |  |
| mandel_2 | safemap_deterministic | 28 | 4 | 0.0 | 9 | 0 | 1 | 0.25 | passed | skipped |
| matmul_f64_4x4 | safemap_deterministic | 72 | 3 | 0.333 | 7 | 0 | 0 | 0.0 |  |  |
| perlin | safemap_deterministic | 81 | 6 | 0.0 | 19 | 1 | 2 | 0.4 | passed | skipped |
| pi | safemap_deterministic | 64 | 2 | 0.5 | 4 | 1 | 0 | 0.0 |  |  |
| revertBits | safemap_deterministic | 67 | 3 | 0.0 | 11 | 0 | 2 | 0.6666666666666666 | passed | skipped |
| salsa20 | safemap_deterministic | 75 | 3 | 0.0 | 9 | 0 | 0 | 0.0 |  |  |

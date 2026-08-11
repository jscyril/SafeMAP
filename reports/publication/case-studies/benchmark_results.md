# SafeMAP Benchmark Summary

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| safemap_deterministic | 6 | `completed`: 6 | 17 | 25 | 0.680 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|
| safemap_deterministic | 20 | 17 | 0.850 | `accepted`: 17, `not_accepted`: 3 |

## Idiom Success

| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |
|---|---|---:|---:|---:|
| safemap_deterministic | boolean_int | 1 | 1 | 1.000 |
| safemap_deterministic | c_string | 3 | 0 | 0.000 |
| safemap_deterministic | error_code_return | 2 | 2 | 1.000 |
| safemap_deterministic | fixed_size_array | 1 | 1 | 1.000 |
| safemap_deterministic | manual_allocation | 4 | 3 | 0.750 |
| safemap_deterministic | nullable_pointer | 2 | 2 | 1.000 |
| safemap_deterministic | output_parameter | 3 | 3 | 1.000 |
| safemap_deterministic | pointer_length_array | 3 | 3 | 1.000 |
| safemap_deterministic | struct_pointer | 1 | 1 | 1.000 |

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|
| safemap_deterministic | c_sanitizers | passed | 6 |
| safemap_deterministic | cargo_check | passed | 6 |
| safemap_deterministic | cargo_test | passed | 6 |
| safemap_deterministic | clippy | passed | 6 |
| safemap_deterministic | differential | not_applicable | 1 |
| safemap_deterministic | differential | passed | 5 |
| safemap_deterministic | miri | skipped | 6 |

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| safemap_deterministic | 157 | 25 | 14 | 25 | 0.560 | 34 | 0 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| allocation_factory | safemap_deterministic | 33 | 4 | 0.0 | 5 | 0 | 3 | 0.75 | passed | skipped |
| buffer_metrics | safemap_deterministic | 28 | 4 | 0.5 | 8 | 0 | 3 | 0.75 | passed | skipped |
| config_options | safemap_deterministic | 22 | 4 | 0.667 | 6 | 0 | 3 | 0.75 | passed | skipped |
| scalar_outputs | safemap_deterministic | 27 | 4 | 0.571 | 5 | 0 | 3 | 0.75 | passed | skipped |
| string_records | safemap_deterministic | 19 | 4 | 1.0 | 4 | 0 | 0 | 0.0 | not_applicable | skipped |
| structured_composition | safemap_deterministic | 28 | 5 | 0.5 | 6 | 0 | 5 | 1.0 | passed | skipped |

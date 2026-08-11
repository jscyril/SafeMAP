# SafeMAP Benchmark Summary

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| safemap_deterministic | 6 | `completed`: 6 | 17 | 25 | 0.680 |
| safemap_without_dependency_grouping | 6 | `completed`: 6 | 15 | 25 | 0.600 |
| safemap_without_idiom_plans | 6 | `completed`: 1, `no_supported_synthesis`: 5 | 1 | 25 | 0.040 |
| safemap_without_pointer_roles | 6 | `completed`: 6 | 3 | 24 | 0.125 |
| safemap_without_safe_signatures | 6 | `completed`: 6 | 0 | 25 | 0.000 |
| safemap_without_validation_feedback | 6 | `completed`: 6 | 17 | 25 | 0.680 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|
| safemap_deterministic | 20 | 17 | 0.850 | `accepted`: 17, `not_accepted`: 3 |
| safemap_without_dependency_grouping | 20 | 15 | 0.750 | `accepted`: 15, `not_accepted`: 5 |
| safemap_without_idiom_plans | 20 | 1 | 0.050 | `accepted`: 1, `not_accepted`: 6, `safe_translatable_with_api_change`: 13 |
| safemap_without_pointer_roles | 20 | 3 | 0.150 | `accepted`: 3, `not_accepted`: 16, `requires_manual_refactor`: 1 |
| safemap_without_safe_signatures | 20 | 0 | 0.000 | `not_accepted`: 20 |
| safemap_without_validation_feedback | 20 | 17 | 0.850 | `accepted`: 17, `not_accepted`: 3 |

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
| safemap_without_dependency_grouping | boolean_int | 1 | 1 | 1.000 |
| safemap_without_dependency_grouping | c_string | 3 | 0 | 0.000 |
| safemap_without_dependency_grouping | error_code_return | 2 | 2 | 1.000 |
| safemap_without_dependency_grouping | fixed_size_array | 1 | 1 | 1.000 |
| safemap_without_dependency_grouping | manual_allocation | 4 | 3 | 0.750 |
| safemap_without_dependency_grouping | nullable_pointer | 2 | 2 | 1.000 |
| safemap_without_dependency_grouping | output_parameter | 3 | 3 | 1.000 |
| safemap_without_dependency_grouping | pointer_length_array | 3 | 3 | 1.000 |
| safemap_without_dependency_grouping | struct_pointer | 1 | 1 | 1.000 |
| safemap_without_pointer_roles | boolean_int | 1 | 0 | 0.000 |
| safemap_without_pointer_roles | c_string | 3 | 0 | 0.000 |
| safemap_without_pointer_roles | error_code_return | 2 | 0 | 0.000 |
| safemap_without_pointer_roles | fixed_size_array | 1 | 0 | 0.000 |
| safemap_without_pointer_roles | manual_allocation | 4 | 3 | 0.750 |
| safemap_without_pointer_roles | nullable_pointer | 2 | 0 | 0.000 |
| safemap_without_pointer_roles | output_parameter | 2 | 0 | 0.000 |
| safemap_without_pointer_roles | pointer_length_array | 3 | 0 | 0.000 |
| safemap_without_pointer_roles | struct_pointer | 1 | 0 | 0.000 |
| safemap_without_safe_signatures | boolean_int | 1 | 0 | 0.000 |
| safemap_without_safe_signatures | c_string | 3 | 0 | 0.000 |
| safemap_without_safe_signatures | error_code_return | 2 | 0 | 0.000 |
| safemap_without_safe_signatures | fixed_size_array | 1 | 0 | 0.000 |
| safemap_without_safe_signatures | manual_allocation | 4 | 0 | 0.000 |
| safemap_without_safe_signatures | nullable_pointer | 2 | 0 | 0.000 |
| safemap_without_safe_signatures | output_parameter | 3 | 0 | 0.000 |
| safemap_without_safe_signatures | pointer_length_array | 3 | 0 | 0.000 |
| safemap_without_safe_signatures | struct_pointer | 1 | 0 | 0.000 |
| safemap_without_validation_feedback | boolean_int | 1 | 1 | 1.000 |
| safemap_without_validation_feedback | c_string | 3 | 0 | 0.000 |
| safemap_without_validation_feedback | error_code_return | 2 | 2 | 1.000 |
| safemap_without_validation_feedback | fixed_size_array | 1 | 1 | 1.000 |
| safemap_without_validation_feedback | manual_allocation | 4 | 3 | 0.750 |
| safemap_without_validation_feedback | nullable_pointer | 2 | 2 | 1.000 |
| safemap_without_validation_feedback | output_parameter | 3 | 3 | 1.000 |
| safemap_without_validation_feedback | pointer_length_array | 3 | 3 | 1.000 |
| safemap_without_validation_feedback | struct_pointer | 1 | 1 | 1.000 |

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
| safemap_without_dependency_grouping | c_sanitizers | passed | 6 |
| safemap_without_dependency_grouping | cargo_check | passed | 6 |
| safemap_without_dependency_grouping | cargo_test | passed | 6 |
| safemap_without_dependency_grouping | clippy | passed | 6 |
| safemap_without_dependency_grouping | differential | not_applicable | 1 |
| safemap_without_dependency_grouping | differential | passed | 5 |
| safemap_without_dependency_grouping | miri | skipped | 6 |
| safemap_without_idiom_plans | c_sanitizers | passed | 1 |
| safemap_without_idiom_plans | cargo_check | passed | 1 |
| safemap_without_idiom_plans | cargo_test | passed | 1 |
| safemap_without_idiom_plans | clippy | passed | 1 |
| safemap_without_idiom_plans | differential | passed | 1 |
| safemap_without_idiom_plans | miri | skipped | 1 |
| safemap_without_pointer_roles | c_sanitizers | passed | 6 |
| safemap_without_pointer_roles | cargo_check | failed | 4 |
| safemap_without_pointer_roles | cargo_check | passed | 2 |
| safemap_without_pointer_roles | cargo_test | failed | 4 |
| safemap_without_pointer_roles | cargo_test | passed | 2 |
| safemap_without_pointer_roles | clippy | failed | 4 |
| safemap_without_pointer_roles | clippy | passed | 2 |
| safemap_without_pointer_roles | differential | failed | 4 |
| safemap_without_pointer_roles | differential | not_applicable | 1 |
| safemap_without_pointer_roles | differential | passed | 1 |
| safemap_without_pointer_roles | miri | skipped | 6 |
| safemap_without_safe_signatures | c_sanitizers | passed | 6 |
| safemap_without_safe_signatures | cargo_check | failed | 6 |
| safemap_without_safe_signatures | cargo_test | failed | 6 |
| safemap_without_safe_signatures | clippy | failed | 6 |
| safemap_without_safe_signatures | differential | failed | 6 |
| safemap_without_safe_signatures | miri | skipped | 6 |
| safemap_without_validation_feedback | c_sanitizers | passed | 6 |
| safemap_without_validation_feedback | cargo_check | passed | 6 |
| safemap_without_validation_feedback | cargo_test | passed | 6 |
| safemap_without_validation_feedback | clippy | passed | 6 |
| safemap_without_validation_feedback | differential | not_applicable | 1 |
| safemap_without_validation_feedback | differential | passed | 5 |
| safemap_without_validation_feedback | miri | skipped | 6 |

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| safemap_deterministic | 157 | 25 | 14 | 25 | 0.560 | 34 | 0 |
| safemap_without_dependency_grouping | 157 | 25 | 14 | 25 | 0.560 | 34 | 0 |
| safemap_without_idiom_plans | 157 | 25 | 14 | 25 | 0.560 | 34 | 0 |
| safemap_without_pointer_roles | 157 | 25 | 14 | 25 | 0.560 | 34 | 0 |
| safemap_without_safe_signatures | 157 | 25 | 14 | 25 | 0.560 | 34 | 0 |
| safemap_without_validation_feedback | 157 | 25 | 14 | 25 | 0.560 | 34 | 0 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| allocation_factory | safemap_deterministic | 33 | 4 | 0.0 | 5 | 0 | 3 | 0.75 | passed | skipped |
| allocation_factory | safemap_without_pointer_roles | 33 | 4 | 0.0 | 5 | 0 | 3 | 0.75 | passed | skipped |
| allocation_factory | safemap_without_safe_signatures | 33 | 4 | 0.0 | 5 | 0 | 0 | 0.0 | failed | skipped |
| allocation_factory | safemap_without_dependency_grouping | 33 | 4 | 0.0 | 5 | 0 | 3 | 0.75 | passed | skipped |
| allocation_factory | safemap_without_idiom_plans | 33 | 4 | 0.0 | 5 | 0 | 0 | 0.0 | None | None |
| allocation_factory | safemap_without_validation_feedback | 33 | 4 | 0.0 | 5 | 0 | 3 | 0.75 | passed | skipped |
| buffer_metrics | safemap_deterministic | 28 | 4 | 0.5 | 8 | 0 | 3 | 0.75 | passed | skipped |
| buffer_metrics | safemap_without_pointer_roles | 28 | 4 | 0.5 | 8 | 0 | 0 | 0.0 | failed | skipped |
| buffer_metrics | safemap_without_safe_signatures | 28 | 4 | 0.5 | 8 | 0 | 0 | 0.0 | failed | skipped |
| buffer_metrics | safemap_without_dependency_grouping | 28 | 4 | 0.5 | 8 | 0 | 3 | 0.75 | passed | skipped |
| buffer_metrics | safemap_without_idiom_plans | 28 | 4 | 0.5 | 8 | 0 | 0 | 0.0 | None | None |
| buffer_metrics | safemap_without_validation_feedback | 28 | 4 | 0.5 | 8 | 0 | 3 | 0.75 | passed | skipped |
| config_options | safemap_deterministic | 22 | 4 | 0.667 | 6 | 0 | 3 | 0.75 | passed | skipped |
| config_options | safemap_without_pointer_roles | 22 | 4 | 0.667 | 6 | 0 | 0 | 0.0 | failed | skipped |
| config_options | safemap_without_safe_signatures | 22 | 4 | 0.667 | 6 | 0 | 0 | 0.0 | failed | skipped |
| config_options | safemap_without_dependency_grouping | 22 | 4 | 0.667 | 6 | 0 | 3 | 0.75 | passed | skipped |
| config_options | safemap_without_idiom_plans | 22 | 4 | 0.667 | 6 | 0 | 0 | 0.0 | None | None |
| config_options | safemap_without_validation_feedback | 22 | 4 | 0.667 | 6 | 0 | 3 | 0.75 | passed | skipped |
| scalar_outputs | safemap_deterministic | 27 | 4 | 0.571 | 5 | 0 | 3 | 0.75 | passed | skipped |
| scalar_outputs | safemap_without_pointer_roles | 27 | 4 | 0.571 | 5 | 0 | 0 | 0.0 | failed | skipped |
| scalar_outputs | safemap_without_safe_signatures | 27 | 4 | 0.571 | 5 | 0 | 0 | 0.0 | failed | skipped |
| scalar_outputs | safemap_without_dependency_grouping | 27 | 4 | 0.571 | 5 | 0 | 3 | 0.75 | passed | skipped |
| scalar_outputs | safemap_without_idiom_plans | 27 | 4 | 0.571 | 5 | 0 | 0 | 0.0 | None | None |
| scalar_outputs | safemap_without_validation_feedback | 27 | 4 | 0.571 | 5 | 0 | 3 | 0.75 | passed | skipped |
| string_records | safemap_deterministic | 19 | 4 | 1.0 | 4 | 0 | 0 | 0.0 | not_applicable | skipped |
| string_records | safemap_without_pointer_roles | 19 | 4 | 1.0 | 4 | 0 | 0 | 0.0 | not_applicable | skipped |
| string_records | safemap_without_safe_signatures | 19 | 4 | 1.0 | 4 | 0 | 0 | 0.0 | failed | skipped |
| string_records | safemap_without_dependency_grouping | 19 | 4 | 1.0 | 4 | 0 | 0 | 0.0 | not_applicable | skipped |
| string_records | safemap_without_idiom_plans | 19 | 4 | 1.0 | 4 | 0 | 0 | 0.0 | None | None |
| string_records | safemap_without_validation_feedback | 19 | 4 | 1.0 | 4 | 0 | 0 | 0.0 | not_applicable | skipped |
| structured_composition | safemap_deterministic | 28 | 5 | 0.5 | 6 | 0 | 5 | 1.0 | passed | skipped |
| structured_composition | safemap_without_pointer_roles | 28 | 5 | 0.5 | 6 | 0 | 0 | 0.0 | failed | skipped |
| structured_composition | safemap_without_safe_signatures | 28 | 5 | 0.5 | 6 | 0 | 0 | 0.0 | failed | skipped |
| structured_composition | safemap_without_dependency_grouping | 28 | 5 | 0.5 | 6 | 0 | 3 | 0.6 | passed | skipped |
| structured_composition | safemap_without_idiom_plans | 28 | 5 | 0.5 | 6 | 0 | 1 | 0.2 | passed | skipped |
| structured_composition | safemap_without_validation_feedback | 28 | 5 | 0.5 | 6 | 0 | 5 | 1.0 | passed | skipped |

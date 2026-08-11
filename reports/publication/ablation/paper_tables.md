# SafeMAP Paper Tables

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| safemap_deterministic | 40 | `completed`: 36, `no_supported_synthesis`: 4 | 36 | 76 | 0.474 |
| safemap_without_dependency_grouping | 40 | `completed`: 36, `no_supported_synthesis`: 4 | 36 | 76 | 0.474 |
| safemap_without_idiom_plans | 40 | `completed`: 6, `no_supported_synthesis`: 34 | 6 | 76 | 0.079 |
| safemap_without_pointer_roles | 40 | `completed`: 24, `no_supported_synthesis`: 16 | 16 | 73 | 0.219 |
| safemap_without_safe_signatures | 40 | `completed`: 35, `no_supported_synthesis`: 5 | 6 | 76 | 0.079 |
| safemap_without_validation_feedback | 40 | `completed`: 36, `no_supported_synthesis`: 4 | 36 | 76 | 0.474 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|
| safemap_deterministic | 40 | 35 | 0.875 | `accepted`: 35, `not_accepted`: 1, `unsupported`: 4 |
| safemap_without_dependency_grouping | 40 | 35 | 0.875 | `accepted`: 35, `not_accepted`: 1, `unsupported`: 4 |
| safemap_without_idiom_plans | 40 | 5 | 0.125 | `accepted`: 5, `not_accepted`: 8, `safe_translatable_with_api_change`: 23, `unsupported`: 4 |
| safemap_without_pointer_roles | 40 | 15 | 0.375 | `accepted`: 15, `not_accepted`: 18, `requires_manual_refactor`: 3, `unsupported`: 4 |
| safemap_without_safe_signatures | 40 | 5 | 0.125 | `accepted`: 5, `not_accepted`: 31, `unsupported`: 4 |
| safemap_without_validation_feedback | 40 | 35 | 0.875 | `accepted`: 35, `not_accepted`: 1, `unsupported`: 4 |

## Idiom Success

| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |
|---|---|---:|---:|---:|
| safemap_deterministic | boolean_int | 5 | 5 | 1.000 |
| safemap_deterministic | c_string | 3 | 2 | 0.667 |
| safemap_deterministic | error_code_return | 4 | 4 | 1.000 |
| safemap_deterministic | manual_allocation | 6 | 3 | 0.500 |
| safemap_deterministic | nullable_pointer | 2 | 2 | 1.000 |
| safemap_deterministic | output_parameter | 11 | 11 | 1.000 |
| safemap_deterministic | pointer_length_array | 8 | 8 | 1.000 |
| safemap_without_dependency_grouping | boolean_int | 5 | 5 | 1.000 |
| safemap_without_dependency_grouping | c_string | 3 | 2 | 0.667 |
| safemap_without_dependency_grouping | error_code_return | 4 | 4 | 1.000 |
| safemap_without_dependency_grouping | manual_allocation | 6 | 3 | 0.500 |
| safemap_without_dependency_grouping | nullable_pointer | 2 | 2 | 1.000 |
| safemap_without_dependency_grouping | output_parameter | 11 | 11 | 1.000 |
| safemap_without_dependency_grouping | pointer_length_array | 8 | 8 | 1.000 |
| safemap_without_pointer_roles | boolean_int | 5 | 5 | 1.000 |
| safemap_without_pointer_roles | c_string | 3 | 2 | 0.667 |
| safemap_without_pointer_roles | error_code_return | 4 | 0 | 0.000 |
| safemap_without_pointer_roles | manual_allocation | 6 | 3 | 0.500 |
| safemap_without_pointer_roles | nullable_pointer | 2 | 0 | 0.000 |
| safemap_without_pointer_roles | output_parameter | 8 | 0 | 0.000 |
| safemap_without_pointer_roles | pointer_length_array | 8 | 0 | 0.000 |
| safemap_without_safe_signatures | boolean_int | 5 | 0 | 0.000 |
| safemap_without_safe_signatures | c_string | 3 | 0 | 0.000 |
| safemap_without_safe_signatures | error_code_return | 4 | 0 | 0.000 |
| safemap_without_safe_signatures | manual_allocation | 6 | 0 | 0.000 |
| safemap_without_safe_signatures | nullable_pointer | 2 | 0 | 0.000 |
| safemap_without_safe_signatures | output_parameter | 11 | 0 | 0.000 |
| safemap_without_safe_signatures | pointer_length_array | 8 | 0 | 0.000 |
| safemap_without_validation_feedback | boolean_int | 5 | 5 | 1.000 |
| safemap_without_validation_feedback | c_string | 3 | 2 | 0.667 |
| safemap_without_validation_feedback | error_code_return | 4 | 4 | 1.000 |
| safemap_without_validation_feedback | manual_allocation | 6 | 3 | 0.500 |
| safemap_without_validation_feedback | nullable_pointer | 2 | 2 | 1.000 |
| safemap_without_validation_feedback | output_parameter | 11 | 11 | 1.000 |
| safemap_without_validation_feedback | pointer_length_array | 8 | 8 | 1.000 |

## Failure Categories

| Mode | Category | Count |
|---|---|---:|
| safemap_deterministic | unsupported | 5 |
| safemap_without_dependency_grouping | unsupported | 5 |
| safemap_without_idiom_plans | unsupported | 5 |
| safemap_without_pointer_roles | behavioral_validation_missing_or_failed | 1 |
| safemap_without_pointer_roles | requires_manual_refactor | 3 |
| safemap_without_pointer_roles | unsupported | 5 |
| safemap_without_pointer_roles | validation_failed | 7 |
| safemap_without_safe_signatures | unsupported | 5 |
| safemap_without_safe_signatures | validation_failed | 29 |
| safemap_without_validation_feedback | unsupported | 5 |

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|
| safemap_deterministic | c_sanitizers | passed | 36 |
| safemap_deterministic | cargo_check | passed | 36 |
| safemap_deterministic | cargo_test | passed | 36 |
| safemap_deterministic | clippy | passed | 36 |
| safemap_deterministic | differential | passed | 36 |
| safemap_deterministic | miri | skipped | 36 |
| safemap_without_dependency_grouping | c_sanitizers | passed | 36 |
| safemap_without_dependency_grouping | cargo_check | passed | 36 |
| safemap_without_dependency_grouping | cargo_test | passed | 36 |
| safemap_without_dependency_grouping | clippy | passed | 36 |
| safemap_without_dependency_grouping | differential | passed | 36 |
| safemap_without_dependency_grouping | miri | skipped | 36 |
| safemap_without_idiom_plans | c_sanitizers | passed | 6 |
| safemap_without_idiom_plans | cargo_check | passed | 6 |
| safemap_without_idiom_plans | cargo_test | passed | 6 |
| safemap_without_idiom_plans | clippy | passed | 6 |
| safemap_without_idiom_plans | differential | passed | 6 |
| safemap_without_idiom_plans | miri | skipped | 6 |
| safemap_without_pointer_roles | c_sanitizers | passed | 24 |
| safemap_without_pointer_roles | cargo_check | failed | 7 |
| safemap_without_pointer_roles | cargo_check | passed | 17 |
| safemap_without_pointer_roles | cargo_test | failed | 7 |
| safemap_without_pointer_roles | cargo_test | passed | 17 |
| safemap_without_pointer_roles | clippy | failed | 7 |
| safemap_without_pointer_roles | clippy | passed | 17 |
| safemap_without_pointer_roles | differential | failed | 7 |
| safemap_without_pointer_roles | differential | not_applicable | 1 |
| safemap_without_pointer_roles | differential | passed | 16 |
| safemap_without_pointer_roles | miri | skipped | 24 |
| safemap_without_safe_signatures | c_sanitizers | passed | 35 |
| safemap_without_safe_signatures | cargo_check | failed | 29 |
| safemap_without_safe_signatures | cargo_check | passed | 6 |
| safemap_without_safe_signatures | cargo_test | failed | 29 |
| safemap_without_safe_signatures | cargo_test | passed | 6 |
| safemap_without_safe_signatures | clippy | failed | 29 |
| safemap_without_safe_signatures | clippy | passed | 6 |
| safemap_without_safe_signatures | differential | failed | 29 |
| safemap_without_safe_signatures | differential | passed | 6 |
| safemap_without_safe_signatures | miri | skipped | 35 |
| safemap_without_validation_feedback | c_sanitizers | passed | 36 |
| safemap_without_validation_feedback | cargo_check | passed | 36 |
| safemap_without_validation_feedback | cargo_test | passed | 36 |
| safemap_without_validation_feedback | clippy | passed | 36 |
| safemap_without_validation_feedback | differential | passed | 36 |
| safemap_without_validation_feedback | miri | skipped | 36 |

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| safemap_deterministic | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| safemap_without_dependency_grouping | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| safemap_without_idiom_plans | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| safemap_without_pointer_roles | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| safemap_without_safe_signatures | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |
| safemap_without_validation_feedback | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| array_max | safemap_deterministic | 15 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| array_max | safemap_without_pointer_roles | 15 | 2 | 0.5 | 4 | 0 | 0 | 0.0 | failed | skipped |
| array_max | safemap_without_safe_signatures | 15 | 2 | 0.5 | 4 | 0 | 0 | 0.0 | failed | skipped |
| array_max | safemap_without_dependency_grouping | 15 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| array_max | safemap_without_idiom_plans | 15 | 2 | 0.5 | 4 | 0 | 0 | 0.0 |  |  |
| array_max | safemap_without_validation_feedback | 15 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| array_total | safemap_deterministic | 13 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| array_total | safemap_without_pointer_roles | 13 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| array_total | safemap_without_safe_signatures | 13 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| array_total | safemap_without_dependency_grouping | 13 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| array_total | safemap_without_idiom_plans | 13 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| array_total | safemap_without_validation_feedback | 13 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| boolean_greater_equal | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_greater_equal | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_greater_equal | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| boolean_greater_equal | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_greater_equal | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_greater_equal | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_int | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_int | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_int | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| boolean_int | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_int | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_int | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_less_equal | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_less_equal | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_less_equal | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| boolean_less_equal | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_less_equal | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_less_equal | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_negative | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_negative | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_negative | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| boolean_negative | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_negative | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_negative | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_nonzero | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_nonzero | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_nonzero | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| boolean_nonzero | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_nonzero | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_nonzero | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| error_code | safemap_deterministic | 15 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| error_code | safemap_without_pointer_roles | 15 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | failed | skipped |
| error_code | safemap_without_safe_signatures | 15 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | failed | skipped |
| error_code | safemap_without_dependency_grouping | 15 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| error_code | safemap_without_idiom_plans | 15 | 2 | 0.333 | 3 | 0 | 0 | 0.0 |  |  |
| error_code | safemap_without_validation_feedback | 15 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| error_code_product | safemap_deterministic | 14 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| error_code_product | safemap_without_pointer_roles | 14 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | failed | skipped |
| error_code_product | safemap_without_safe_signatures | 14 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | failed | skipped |
| error_code_product | safemap_without_dependency_grouping | 14 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| error_code_product | safemap_without_idiom_plans | 14 | 2 | 0.333 | 3 | 0 | 0 | 0.0 |  |  |
| error_code_product | safemap_without_validation_feedback | 14 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free | safemap_deterministic | 18 | 2 | 0.0 | 4 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free | safemap_without_pointer_roles | 18 | 2 | 0.0 | 4 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free | safemap_without_safe_signatures | 18 | 2 | 0.0 | 4 | 0 | 0 | 0.0 | failed | skipped |
| malloc_free | safemap_without_dependency_grouping | 18 | 2 | 0.0 | 4 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free | safemap_without_idiom_plans | 18 | 2 | 0.0 | 4 | 0 | 0 | 0.0 |  |  |
| malloc_free | safemap_without_validation_feedback | 18 | 2 | 0.0 | 4 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free_constant | safemap_deterministic | 15 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free_constant | safemap_without_pointer_roles | 15 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free_constant | safemap_without_safe_signatures | 15 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| malloc_free_constant | safemap_without_dependency_grouping | 15 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free_constant | safemap_without_idiom_plans | 15 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| malloc_free_constant | safemap_without_validation_feedback | 15 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| malloc_vec | safemap_deterministic | 20 | 2 | 0.0 | 5 | 0 | 1 | 0.5 | passed | skipped |
| malloc_vec | safemap_without_pointer_roles | 20 | 2 | 0.0 | 5 | 0 | 1 | 0.5 | passed | skipped |
| malloc_vec | safemap_without_safe_signatures | 20 | 2 | 0.0 | 5 | 0 | 0 | 0.0 |  |  |
| malloc_vec | safemap_without_dependency_grouping | 20 | 2 | 0.0 | 5 | 0 | 1 | 0.5 | passed | skipped |
| malloc_vec | safemap_without_idiom_plans | 20 | 2 | 0.0 | 5 | 0 | 0 | 0.0 |  |  |
| malloc_vec | safemap_without_validation_feedback | 20 | 2 | 0.0 | 5 | 0 | 1 | 0.5 | passed | skipped |
| min_max_outputs | safemap_deterministic | 14 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| min_max_outputs | safemap_without_pointer_roles | 14 | 2 | 0.5 | 4 | 0 | 0 | 0.0 |  |  |
| min_max_outputs | safemap_without_safe_signatures | 14 | 2 | 0.5 | 4 | 0 | 0 | 0.0 | failed | skipped |
| min_max_outputs | safemap_without_dependency_grouping | 14 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| min_max_outputs | safemap_without_idiom_plans | 14 | 2 | 0.5 | 4 | 0 | 0 | 0.0 |  |  |
| min_max_outputs | safemap_without_validation_feedback | 14 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| multiple_outputs | safemap_deterministic | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| multiple_outputs | safemap_without_pointer_roles | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| multiple_outputs | safemap_without_safe_signatures | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | failed | skipped |
| multiple_outputs | safemap_without_dependency_grouping | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| multiple_outputs | safemap_without_idiom_plans | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| multiple_outputs | safemap_without_validation_feedback | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer | safemap_without_pointer_roles | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer | safemap_without_safe_signatures | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| mutable_buffer | safemap_without_dependency_grouping | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer | safemap_without_idiom_plans | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer | safemap_without_validation_feedback | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_add_two | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_add_two | safemap_without_pointer_roles | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_add_two | safemap_without_safe_signatures | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| mutable_buffer_add_two | safemap_without_dependency_grouping | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_add_two | safemap_without_idiom_plans | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_add_two | safemap_without_validation_feedback | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_decrement | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_decrement | safemap_without_pointer_roles | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_decrement | safemap_without_safe_signatures | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| mutable_buffer_decrement | safemap_without_dependency_grouping | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_decrement | safemap_without_idiom_plans | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_decrement | safemap_without_validation_feedback | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_subtract_two | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_subtract_two | safemap_without_pointer_roles | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_subtract_two | safemap_without_safe_signatures | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| mutable_buffer_subtract_two | safemap_without_dependency_grouping | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_subtract_two | safemap_without_idiom_plans | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_subtract_two | safemap_without_validation_feedback | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer | safemap_deterministic | 14 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer | safemap_without_pointer_roles | 14 | 2 | 1.0 | 3 | 0 | 0 | 0.0 | failed | skipped |
| nullable_pointer | safemap_without_safe_signatures | 14 | 2 | 1.0 | 3 | 0 | 0 | 0.0 | failed | skipped |
| nullable_pointer | safemap_without_dependency_grouping | 14 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer | safemap_without_idiom_plans | 14 | 2 | 1.0 | 3 | 0 | 0 | 0.0 |  |  |
| nullable_pointer | safemap_without_validation_feedback | 14 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer_zero | safemap_deterministic | 13 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer_zero | safemap_without_pointer_roles | 13 | 2 | 1.0 | 3 | 0 | 0 | 0.0 | not_applicable | skipped |
| nullable_pointer_zero | safemap_without_safe_signatures | 13 | 2 | 1.0 | 3 | 0 | 0 | 0.0 | failed | skipped |
| nullable_pointer_zero | safemap_without_dependency_grouping | 13 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer_zero | safemap_without_idiom_plans | 13 | 2 | 1.0 | 3 | 0 | 0 | 0.0 |  |  |
| nullable_pointer_zero | safemap_without_validation_feedback | 13 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| output_double | safemap_deterministic | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| output_double | safemap_without_pointer_roles | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| output_double | safemap_without_safe_signatures | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | failed | skipped |
| output_double | safemap_without_dependency_grouping | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| output_double | safemap_without_idiom_plans | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| output_double | safemap_without_validation_feedback | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| output_parameter | safemap_deterministic | 18 | 2 | 0.667 | 5 | 0 | 1 | 0.5 | passed | skipped |
| output_parameter | safemap_without_pointer_roles | 18 | 2 | 0.667 | 5 | 0 | 0 | 0.0 | failed | skipped |
| output_parameter | safemap_without_safe_signatures | 18 | 2 | 0.667 | 5 | 0 | 0 | 0.0 | failed | skipped |
| output_parameter | safemap_without_dependency_grouping | 18 | 2 | 0.667 | 5 | 0 | 1 | 0.5 | passed | skipped |
| output_parameter | safemap_without_idiom_plans | 18 | 2 | 0.667 | 5 | 0 | 0 | 0.0 |  |  |
| output_parameter | safemap_without_validation_feedback | 18 | 2 | 0.667 | 5 | 0 | 1 | 0.5 | passed | skipped |
| output_square | safemap_deterministic | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| output_square | safemap_without_pointer_roles | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| output_square | safemap_without_safe_signatures | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | failed | skipped |
| output_square | safemap_without_dependency_grouping | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| output_square | safemap_without_idiom_plans | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| output_square | safemap_without_validation_feedback | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| pointer_length_array | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| pointer_length_array | safemap_without_pointer_roles | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| pointer_length_array | safemap_without_safe_signatures | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| pointer_length_array | safemap_without_dependency_grouping | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| pointer_length_array | safemap_without_idiom_plans | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| pointer_length_array | safemap_without_validation_feedback | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| simple_divide | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_divide | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_divide | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_divide | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_divide | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_divide | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_modulo | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_modulo | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_modulo | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_modulo | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_modulo | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_modulo | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_multiply | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_multiply | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_multiply | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_multiply | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_multiply | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_multiply | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer | safemap_deterministic | 13 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer | safemap_without_pointer_roles | 13 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer | safemap_without_safe_signatures | 13 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_pointer | safemap_without_dependency_grouping | 13 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer | safemap_without_idiom_plans | 13 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer | safemap_without_validation_feedback | 13 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_decrement | safemap_deterministic | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_decrement | safemap_without_pointer_roles | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer_decrement | safemap_without_safe_signatures | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_pointer_decrement | safemap_without_dependency_grouping | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_decrement | safemap_without_idiom_plans | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer_decrement | safemap_without_validation_feedback | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_double | safemap_deterministic | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_double | safemap_without_pointer_roles | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer_double | safemap_without_safe_signatures | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_pointer_double | safemap_without_dependency_grouping | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_double | safemap_without_idiom_plans | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer_double | safemap_without_validation_feedback | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_subtract | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_subtract | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_subtract | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_subtract | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_subtract | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_subtract | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_sum | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_sum | safemap_without_pointer_roles | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_sum | safemap_without_safe_signatures | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_sum | safemap_without_dependency_grouping | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_sum | safemap_without_idiom_plans | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_sum | safemap_without_validation_feedback | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length | safemap_deterministic | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length | safemap_without_pointer_roles | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length | safemap_without_safe_signatures | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| string_length | safemap_without_dependency_grouping | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length | safemap_without_idiom_plans | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length | safemap_without_validation_feedback | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length_long | safemap_deterministic | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length_long | safemap_without_pointer_roles | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length_long | safemap_without_safe_signatures | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| string_length_long | safemap_without_dependency_grouping | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length_long | safemap_without_idiom_plans | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_long | safemap_without_validation_feedback | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length_size_t | safemap_deterministic | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_size_t | safemap_without_pointer_roles | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_size_t | safemap_without_safe_signatures | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_size_t | safemap_without_dependency_grouping | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_size_t | safemap_without_idiom_plans | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_size_t | safemap_without_validation_feedback | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| sum_diff_outputs | safemap_deterministic | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| sum_diff_outputs | safemap_without_pointer_roles | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| sum_diff_outputs | safemap_without_safe_signatures | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | failed | skipped |
| sum_diff_outputs | safemap_without_dependency_grouping | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| sum_diff_outputs | safemap_without_idiom_plans | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| sum_diff_outputs | safemap_without_validation_feedback | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| unsupported_function_pointer | safemap_deterministic | 14 | 3 | 0.2 | 3 | 1 | 1 | 0.5 | passed | skipped |
| unsupported_function_pointer | safemap_without_pointer_roles | 14 | 3 | 0.2 | 3 | 1 | 1 | 0.5 | passed | skipped |
| unsupported_function_pointer | safemap_without_safe_signatures | 14 | 3 | 0.2 | 3 | 1 | 1 | 0.5 | passed | skipped |
| unsupported_function_pointer | safemap_without_dependency_grouping | 14 | 3 | 0.2 | 3 | 1 | 1 | 0.5 | passed | skipped |
| unsupported_function_pointer | safemap_without_idiom_plans | 14 | 3 | 0.2 | 3 | 1 | 1 | 0.5 | passed | skipped |
| unsupported_function_pointer | safemap_without_validation_feedback | 14 | 3 | 0.2 | 3 | 1 | 1 | 0.5 | passed | skipped |
| unsupported_inline_asm | safemap_deterministic | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_inline_asm | safemap_without_pointer_roles | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_inline_asm | safemap_without_safe_signatures | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_inline_asm | safemap_without_dependency_grouping | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_inline_asm | safemap_without_idiom_plans | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_inline_asm | safemap_without_validation_feedback | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_union | safemap_deterministic | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 |  |  |
| unsupported_union | safemap_without_pointer_roles | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 |  |  |
| unsupported_union | safemap_without_safe_signatures | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 |  |  |
| unsupported_union | safemap_without_dependency_grouping | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 |  |  |
| unsupported_union | safemap_without_idiom_plans | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 |  |  |
| unsupported_union | safemap_without_validation_feedback | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 |  |  |
| unsupported_volatile | safemap_deterministic | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_volatile | safemap_without_pointer_roles | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_volatile | safemap_without_safe_signatures | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_volatile | safemap_without_dependency_grouping | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_volatile | safemap_without_idiom_plans | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_volatile | safemap_without_validation_feedback | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 |  |  |

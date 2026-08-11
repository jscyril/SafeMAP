# SafeMAP Paper Tables

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| c2rust_only | 3 | `completed`: 3 | 0 | 70 | 0.000 |
| llm_only | 3 | `completed`: 1, `no_final_output`: 2 | 0 | 70 | 0.000 |
| safemap_deterministic | 3 | `completed`: 2, `no_supported_synthesis`: 1 | 0 | 70 | 0.000 |
| safemap_without_dependency_grouping | 3 | `completed`: 2, `no_supported_synthesis`: 1 | 0 | 70 | 0.000 |
| safemap_without_idiom_plans | 3 | `completed`: 1, `no_supported_synthesis`: 2 | 0 | 70 | 0.000 |
| safemap_without_pointer_roles | 3 | `completed`: 3 | 0 | 115 | 0.000 |
| safemap_without_safe_signatures | 3 | `completed`: 2, `no_supported_synthesis`: 1 | 0 | 70 | 0.000 |
| safemap_without_validation_feedback | 3 | `completed`: 2, `no_supported_synthesis`: 1 | 0 | 70 | 0.000 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|

## Idiom Success

| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |
|---|---|---:|---:|---:|
| safemap_deterministic | boolean_int | 11 | 0 | 0.000 |
| safemap_deterministic | c_string | 3 | 0 | 0.000 |
| safemap_deterministic | error_code_return | 4 | 0 | 0.000 |
| safemap_deterministic | nullable_pointer | 34 | 0 | 0.000 |
| safemap_deterministic | output_parameter | 3 | 0 | 0.000 |
| safemap_deterministic | pointer_length_array | 1 | 0 | 0.000 |
| safemap_deterministic | struct_pointer | 16 | 0 | 0.000 |
| safemap_without_dependency_grouping | boolean_int | 11 | 0 | 0.000 |
| safemap_without_dependency_grouping | c_string | 3 | 0 | 0.000 |
| safemap_without_dependency_grouping | error_code_return | 4 | 0 | 0.000 |
| safemap_without_dependency_grouping | nullable_pointer | 35 | 0 | 0.000 |
| safemap_without_dependency_grouping | output_parameter | 3 | 0 | 0.000 |
| safemap_without_dependency_grouping | pointer_length_array | 1 | 0 | 0.000 |
| safemap_without_dependency_grouping | struct_pointer | 17 | 0 | 0.000 |
| safemap_without_pointer_roles | boolean_int | 11 | 0 | 0.000 |
| safemap_without_pointer_roles | c_string | 5 | 0 | 0.000 |
| safemap_without_pointer_roles | error_code_return | 4 | 0 | 0.000 |
| safemap_without_pointer_roles | nullable_pointer | 40 | 0 | 0.000 |
| safemap_without_pointer_roles | output_parameter | 5 | 0 | 0.000 |
| safemap_without_pointer_roles | pointer_length_array | 1 | 0 | 0.000 |
| safemap_without_pointer_roles | struct_pointer | 17 | 0 | 0.000 |
| safemap_without_safe_signatures | boolean_int | 11 | 0 | 0.000 |
| safemap_without_safe_signatures | c_string | 3 | 0 | 0.000 |
| safemap_without_safe_signatures | error_code_return | 4 | 0 | 0.000 |
| safemap_without_safe_signatures | nullable_pointer | 34 | 0 | 0.000 |
| safemap_without_safe_signatures | output_parameter | 3 | 0 | 0.000 |
| safemap_without_safe_signatures | pointer_length_array | 1 | 0 | 0.000 |
| safemap_without_safe_signatures | struct_pointer | 16 | 0 | 0.000 |
| safemap_without_validation_feedback | boolean_int | 11 | 0 | 0.000 |
| safemap_without_validation_feedback | c_string | 3 | 0 | 0.000 |
| safemap_without_validation_feedback | error_code_return | 4 | 0 | 0.000 |
| safemap_without_validation_feedback | nullable_pointer | 34 | 0 | 0.000 |
| safemap_without_validation_feedback | output_parameter | 3 | 0 | 0.000 |
| safemap_without_validation_feedback | pointer_length_array | 1 | 0 | 0.000 |
| safemap_without_validation_feedback | struct_pointer | 16 | 0 | 0.000 |

## Failure Categories

| Mode | Category | Count |
|---|---|---:|
| c2rust_only | requires_manual_refactor | 46 |
| c2rust_only | unsafe_required | 8 |
| c2rust_only | unsupported | 22 |
| llm_only | requires_manual_refactor | 46 |
| llm_only | unsafe_required | 8 |
| llm_only | unsupported | 22 |
| safemap_deterministic | requires_manual_refactor | 46 |
| safemap_deterministic | unsafe_required | 8 |
| safemap_deterministic | unsupported | 22 |
| safemap_deterministic | validation_failed | 17 |
| safemap_without_dependency_grouping | requires_manual_refactor | 46 |
| safemap_without_dependency_grouping | unsafe_required | 8 |
| safemap_without_dependency_grouping | unsupported | 22 |
| safemap_without_dependency_grouping | validation_failed | 17 |
| safemap_without_idiom_plans | requires_manual_refactor | 46 |
| safemap_without_idiom_plans | unsafe_required | 8 |
| safemap_without_idiom_plans | unsupported | 22 |
| safemap_without_idiom_plans | validation_failed | 1 |
| safemap_without_pointer_roles | requires_manual_refactor | 1 |
| safemap_without_pointer_roles | unsafe_required | 8 |
| safemap_without_pointer_roles | unsupported | 22 |
| safemap_without_pointer_roles | validation_failed | 10 |
| safemap_without_safe_signatures | requires_manual_refactor | 46 |
| safemap_without_safe_signatures | unsafe_required | 8 |
| safemap_without_safe_signatures | unsupported | 22 |
| safemap_without_safe_signatures | validation_failed | 17 |
| safemap_without_validation_feedback | requires_manual_refactor | 46 |
| safemap_without_validation_feedback | unsafe_required | 8 |
| safemap_without_validation_feedback | unsupported | 22 |
| safemap_without_validation_feedback | validation_failed | 17 |

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|
| llm_only | c_sanitizers | unsupported | 1 |
| llm_only | cargo_check | failed | 1 |
| llm_only | cargo_test | failed | 1 |
| llm_only | clippy | failed | 1 |
| llm_only | differential | failed | 1 |
| llm_only | miri | skipped | 1 |
| safemap_deterministic | c_sanitizers | unsupported | 2 |
| safemap_deterministic | cargo_check | failed | 2 |
| safemap_deterministic | cargo_test | failed | 2 |
| safemap_deterministic | clippy | failed | 2 |
| safemap_deterministic | differential | failed | 2 |
| safemap_deterministic | miri | skipped | 2 |
| safemap_without_dependency_grouping | c_sanitizers | unsupported | 2 |
| safemap_without_dependency_grouping | cargo_check | failed | 2 |
| safemap_without_dependency_grouping | cargo_test | failed | 2 |
| safemap_without_dependency_grouping | clippy | failed | 2 |
| safemap_without_dependency_grouping | differential | failed | 2 |
| safemap_without_dependency_grouping | miri | skipped | 2 |
| safemap_without_idiom_plans | c_sanitizers | unsupported | 1 |
| safemap_without_idiom_plans | cargo_check | failed | 1 |
| safemap_without_idiom_plans | cargo_test | failed | 1 |
| safemap_without_idiom_plans | clippy | failed | 1 |
| safemap_without_idiom_plans | differential | failed | 1 |
| safemap_without_idiom_plans | miri | skipped | 1 |
| safemap_without_pointer_roles | c_sanitizers | unsupported | 3 |
| safemap_without_pointer_roles | cargo_check | failed | 3 |
| safemap_without_pointer_roles | cargo_test | failed | 3 |
| safemap_without_pointer_roles | clippy | failed | 3 |
| safemap_without_pointer_roles | differential | failed | 3 |
| safemap_without_pointer_roles | miri | skipped | 3 |
| safemap_without_safe_signatures | c_sanitizers | unsupported | 2 |
| safemap_without_safe_signatures | cargo_check | failed | 2 |
| safemap_without_safe_signatures | cargo_test | failed | 2 |
| safemap_without_safe_signatures | clippy | failed | 2 |
| safemap_without_safe_signatures | differential | failed | 2 |
| safemap_without_safe_signatures | miri | skipped | 2 |
| safemap_without_validation_feedback | c_sanitizers | unsupported | 2 |
| safemap_without_validation_feedback | cargo_check | failed | 2 |
| safemap_without_validation_feedback | cargo_test | failed | 2 |
| safemap_without_validation_feedback | clippy | failed | 2 |
| safemap_without_validation_feedback | differential | failed | 2 |
| safemap_without_validation_feedback | miri | skipped | 2 |

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| c2rust_only | 4062 | 146 | 229 | 282 | 0.812 | 851 | 22 |
| llm_only | 4062 | 146 | 229 | 282 | 0.812 | 851 | 22 |
| safemap_deterministic | 4062 | 146 | 229 | 282 | 0.812 | 851 | 22 |
| safemap_without_dependency_grouping | 4062 | 146 | 229 | 282 | 0.812 | 851 | 22 |
| safemap_without_idiom_plans | 4062 | 146 | 229 | 282 | 0.812 | 851 | 22 |
| safemap_without_pointer_roles | 4062 | 146 | 229 | 282 | 0.812 | 851 | 22 |
| safemap_without_safe_signatures | 4062 | 146 | 229 | 282 | 0.812 | 851 | 22 |
| safemap_without_validation_feedback | 4062 | 146 | 229 | 282 | 0.812 | 851 | 22 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| cjson | c2rust_only | 3191 | 113 | 0.827 | 632 | 15 | 0 | 0.0 |  |  |
| cjson | llm_only | 3191 | 113 | 0.827 | 632 | 15 | 0 | 0.0 |  |  |
| cjson | safemap_deterministic | 3191 | 113 | 0.827 | 632 | 15 | 0 | 0.0 | failed | skipped |
| cjson | safemap_without_dependency_grouping | 3191 | 113 | 0.827 | 632 | 15 | 0 | 0.0 | failed | skipped |
| cjson | safemap_without_idiom_plans | 3191 | 113 | 0.827 | 632 | 15 | 0 | 0.0 | failed | skipped |
| cjson | safemap_without_pointer_roles | 3191 | 113 | 0.827 | 632 | 15 | 0 | 0.0 | failed | skipped |
| cjson | safemap_without_safe_signatures | 3191 | 113 | 0.827 | 632 | 15 | 0 | 0.0 | failed | skipped |
| cjson | safemap_without_validation_feedback | 3191 | 113 | 0.827 | 632 | 15 | 0 | 0.0 | failed | skipped |
| inih | c2rust_only | 326 | 10 | 0.893 | 87 | 1 | 0 | 0.0 |  |  |
| inih | llm_only | 326 | 10 | 0.893 | 87 | 1 | 0 | 0.0 | failed | skipped |
| inih | safemap_deterministic | 326 | 10 | 0.893 | 87 | 1 | 0 | 0.0 |  |  |
| inih | safemap_without_dependency_grouping | 326 | 10 | 0.893 | 87 | 1 | 0 | 0.0 |  |  |
| inih | safemap_without_idiom_plans | 326 | 10 | 0.893 | 87 | 1 | 0 | 0.0 |  |  |
| inih | safemap_without_pointer_roles | 326 | 10 | 0.893 | 87 | 1 | 0 | 0.0 | failed | skipped |
| inih | safemap_without_safe_signatures | 326 | 10 | 0.893 | 87 | 1 | 0 | 0.0 |  |  |
| inih | safemap_without_validation_feedback | 326 | 10 | 0.893 | 87 | 1 | 0 | 0.0 |  |  |
| libcsv | c2rust_only | 545 | 23 | 0.712 | 132 | 6 | 0 | 0.0 |  |  |
| libcsv | llm_only | 545 | 23 | 0.712 | 132 | 6 | 0 | 0.0 |  |  |
| libcsv | safemap_deterministic | 545 | 23 | 0.712 | 132 | 6 | 0 | 0.0 | failed | skipped |
| libcsv | safemap_without_dependency_grouping | 545 | 23 | 0.712 | 132 | 6 | 0 | 0.0 | failed | skipped |
| libcsv | safemap_without_idiom_plans | 545 | 23 | 0.712 | 132 | 6 | 0 | 0.0 |  |  |
| libcsv | safemap_without_pointer_roles | 545 | 23 | 0.712 | 132 | 6 | 0 | 0.0 | failed | skipped |
| libcsv | safemap_without_safe_signatures | 545 | 23 | 0.712 | 132 | 6 | 0 | 0.0 | failed | skipped |
| libcsv | safemap_without_validation_feedback | 545 | 23 | 0.712 | 132 | 6 | 0 | 0.0 | failed | skipped |

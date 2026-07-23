# SafeMAP Paper Tables

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| safemap_full | 40 | `completed`: 40 | 37 | 76 | 0.487 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|
| safemap_full | 40 | 36 | 0.900 | `accepted`: 36, `unsupported`: 4 |

## Idiom Success

| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |
|---|---|---:|---:|---:|
| safemap_full | boolean_int | 5 | 5 | 1.000 |
| safemap_full | c_string | 3 | 3 | 1.000 |
| safemap_full | error_code_return | 4 | 4 | 1.000 |
| safemap_full | manual_allocation | 6 | 3 | 0.500 |
| safemap_full | nullable_pointer | 2 | 2 | 1.000 |
| safemap_full | output_parameter | 11 | 11 | 1.000 |
| safemap_full | pointer_length_array | 8 | 8 | 1.000 |

## Failure Categories

| Mode | Category | Count |
|---|---|---:|
| safemap_full | unsupported | 5 |

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|
| safemap_full | cargo_check | failed | 2 |
| safemap_full | cargo_check | passed | 38 |
| safemap_full | cargo_test | failed | 2 |
| safemap_full | cargo_test | passed | 38 |
| safemap_full | clippy | failed | 2 |
| safemap_full | clippy | passed | 38 |
| safemap_full | differential | failed | 2 |
| safemap_full | differential | not_applicable | 1 |
| safemap_full | differential | passed | 37 |
| safemap_full | miri | skipped | 40 |

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| safemap_full | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| array_max | safemap_full | 15 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| array_total | safemap_full | 13 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| boolean_greater_equal | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_int | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_less_equal | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_negative | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_nonzero | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| error_code | safemap_full | 15 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| error_code_product | safemap_full | 14 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free | safemap_full | 18 | 2 | 0.0 | 4 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free_constant | safemap_full | 15 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| malloc_vec | safemap_full | 20 | 2 | 0.0 | 5 | 0 | 1 | 0.5 | passed | skipped |
| min_max_outputs | safemap_full | 14 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| multiple_outputs | safemap_full | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer | safemap_full | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_add_two | safemap_full | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_decrement | safemap_full | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_subtract_two | safemap_full | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer | safemap_full | 14 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer_zero | safemap_full | 13 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| output_double | safemap_full | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| output_parameter | safemap_full | 18 | 2 | 0.667 | 5 | 0 | 1 | 0.5 | passed | skipped |
| output_square | safemap_full | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| pointer_length_array | safemap_full | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| simple_divide | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_modulo | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_multiply | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer | safemap_full | 13 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_decrement | safemap_full | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_double | safemap_full | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_subtract | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_sum | safemap_full | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length | safemap_full | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length_long | safemap_full | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length_size_t | safemap_full | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| sum_diff_outputs | safemap_full | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| unsupported_function_pointer | safemap_full | 14 | 3 | 0.2 | 3 | 1 | 1 | 0.5 | not_applicable | skipped |
| unsupported_inline_asm | safemap_full | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 | failed | skipped |
| unsupported_union | safemap_full | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 | passed | skipped |
| unsupported_volatile | safemap_full | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 | failed | skipped |

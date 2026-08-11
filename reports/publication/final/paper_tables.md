# SafeMAP Paper Tables

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| safemap_deterministic | 40 | `completed`: 36, `no_supported_synthesis`: 4 | 36 | 76 | 0.474 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|
| safemap_deterministic | 40 | 35 | 0.875 | `accepted`: 35, `not_accepted`: 1, `unsupported`: 4 |

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

## Failure Categories

| Mode | Category | Count |
|---|---|---:|
| safemap_deterministic | unsupported | 5 |

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|
| safemap_deterministic | c_sanitizers | passed | 36 |
| safemap_deterministic | cargo_check | passed | 36 |
| safemap_deterministic | cargo_test | passed | 36 |
| safemap_deterministic | clippy | passed | 36 |
| safemap_deterministic | differential | passed | 36 |
| safemap_deterministic | miri | skipped | 36 |

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| safemap_deterministic | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| array_max | safemap_deterministic | 15 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| array_total | safemap_deterministic | 13 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| boolean_greater_equal | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_int | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_less_equal | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_negative | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| boolean_nonzero | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| error_code | safemap_deterministic | 15 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| error_code_product | safemap_deterministic | 14 | 2 | 0.333 | 3 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free | safemap_deterministic | 18 | 2 | 0.0 | 4 | 0 | 1 | 0.5 | passed | skipped |
| malloc_free_constant | safemap_deterministic | 15 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| malloc_vec | safemap_deterministic | 20 | 2 | 0.0 | 5 | 0 | 1 | 0.5 | passed | skipped |
| min_max_outputs | safemap_deterministic | 14 | 2 | 0.5 | 4 | 0 | 1 | 0.5 | passed | skipped |
| multiple_outputs | safemap_deterministic | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_add_two | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_decrement | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| mutable_buffer_subtract_two | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer | safemap_deterministic | 14 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| nullable_pointer_zero | safemap_deterministic | 13 | 2 | 1.0 | 3 | 0 | 1 | 0.5 | passed | skipped |
| output_double | safemap_deterministic | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| output_parameter | safemap_deterministic | 18 | 2 | 0.667 | 5 | 0 | 1 | 0.5 | passed | skipped |
| output_square | safemap_deterministic | 12 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| pointer_length_array | safemap_deterministic | 14 | 2 | 0.5 | 3 | 0 | 1 | 0.5 | passed | skipped |
| simple_divide | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_modulo | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_multiply | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer | safemap_deterministic | 13 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_decrement | safemap_deterministic | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_pointer_double | safemap_deterministic | 12 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_subtract | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| simple_sum | safemap_deterministic | 10 | 2 | 0.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length | safemap_deterministic | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length_long | safemap_deterministic | 11 | 2 | 1.0 | 2 | 0 | 1 | 0.5 | passed | skipped |
| string_length_size_t | safemap_deterministic | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| sum_diff_outputs | safemap_deterministic | 14 | 2 | 0.5 | 2 | 0 | 1 | 0.5 | passed | skipped |
| unsupported_function_pointer | safemap_deterministic | 14 | 3 | 0.2 | 3 | 1 | 1 | 0.5 | passed | skipped |
| unsupported_inline_asm | safemap_deterministic | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_union | safemap_deterministic | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 |  |  |
| unsupported_volatile | safemap_deterministic | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 |  |  |

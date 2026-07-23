# SafeMAP Benchmark Summary

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| c2rust_only | 40 | `completed`: 38, `failed`: 2 | 0 | 72 | 0.000 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|
| c2rust_only | 40 | 0 | 0.000 | `failed`: 2, `not_accepted`: 38 |

## Idiom Success

| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |
|---|---|---:|---:|---:|

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|
| c2rust_only | cargo_check | failed | 35 |
| c2rust_only | cargo_test | failed | 35 |
| c2rust_only | clippy | failed | 35 |
| c2rust_only | differential | failed | 35 |
| c2rust_only | miri | skipped | 35 |

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| c2rust_only | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| array_max | c2rust_only | 15 | 2 | 0.5 | 4 | 0 | 0 | 0.0 | failed | skipped |
| array_total | c2rust_only | 13 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| boolean_greater_equal | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| boolean_int | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| boolean_less_equal | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| boolean_negative | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| boolean_nonzero | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| error_code | c2rust_only | 15 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | failed | skipped |
| error_code_product | c2rust_only | 14 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | failed | skipped |
| malloc_free | c2rust_only | 18 | 2 | 0.0 | 4 | 0 | 0 | 0.0 | failed | skipped |
| malloc_free_constant | c2rust_only | 15 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| malloc_vec | c2rust_only | 20 | 2 | 0.0 | 5 | 0 | 0 | 0.0 | None | None |
| min_max_outputs | c2rust_only | 14 | 2 | 0.5 | 4 | 0 | 0 | 0.0 | failed | skipped |
| multiple_outputs | c2rust_only | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | failed | skipped |
| mutable_buffer | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| mutable_buffer_add_two | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| mutable_buffer_decrement | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| mutable_buffer_subtract_two | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| nullable_pointer | c2rust_only | 14 | 2 | 1.0 | 3 | 0 |  |  |  |  |
| nullable_pointer_zero | c2rust_only | 13 | 2 | 1.0 | 3 | 0 |  |  |  |  |
| output_double | c2rust_only | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | failed | skipped |
| output_parameter | c2rust_only | 18 | 2 | 0.667 | 5 | 0 | 0 | 0.0 | failed | skipped |
| output_square | c2rust_only | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | failed | skipped |
| pointer_length_array | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | failed | skipped |
| simple_divide | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_modulo | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_multiply | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_pointer | c2rust_only | 13 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_pointer_decrement | c2rust_only | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_pointer_double | c2rust_only | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_subtract | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| simple_sum | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| string_length | c2rust_only | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| string_length_long | c2rust_only | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| string_length_size_t | c2rust_only | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | failed | skipped |
| sum_diff_outputs | c2rust_only | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | failed | skipped |
| unsupported_function_pointer | c2rust_only | 14 | 3 | 0.2 | 3 | 1 | 0 | 0.0 | failed | skipped |
| unsupported_inline_asm | c2rust_only | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 | failed | skipped |
| unsupported_union | c2rust_only | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 | None | None |
| unsupported_volatile | c2rust_only | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 | None | None |

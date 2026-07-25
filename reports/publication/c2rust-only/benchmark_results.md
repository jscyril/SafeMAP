# SafeMAP Benchmark Summary

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| c2rust_only | 40 | `completed`: 40 | 0 | 76 | 0.000 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|
| c2rust_only | 40 | 0 | 0.000 | `not_accepted`: 40 |

## Idiom Success

| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |
|---|---|---:|---:|---:|

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| c2rust_only | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| array_max | c2rust_only | 15 | 2 | 0.5 | 4 | 0 | 0 | 0.0 | None | None |
| array_total | c2rust_only | 13 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| boolean_greater_equal | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| boolean_int | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| boolean_less_equal | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| boolean_negative | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| boolean_nonzero | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| error_code | c2rust_only | 15 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | None | None |
| error_code_product | c2rust_only | 14 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | None | None |
| malloc_free | c2rust_only | 18 | 2 | 0.0 | 4 | 0 | 0 | 0.0 | None | None |
| malloc_free_constant | c2rust_only | 15 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| malloc_vec | c2rust_only | 20 | 2 | 0.0 | 5 | 0 | 0 | 0.0 | None | None |
| min_max_outputs | c2rust_only | 14 | 2 | 0.5 | 4 | 0 | 0 | 0.0 | None | None |
| multiple_outputs | c2rust_only | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | None | None |
| mutable_buffer | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| mutable_buffer_add_two | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| mutable_buffer_decrement | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| mutable_buffer_subtract_two | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| nullable_pointer | c2rust_only | 14 | 2 | 1.0 | 3 | 0 | 0 | 0.0 | None | None |
| nullable_pointer_zero | c2rust_only | 13 | 2 | 1.0 | 3 | 0 | 0 | 0.0 | None | None |
| output_double | c2rust_only | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | None | None |
| output_parameter | c2rust_only | 18 | 2 | 0.667 | 5 | 0 | 0 | 0.0 | None | None |
| output_square | c2rust_only | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | None | None |
| pointer_length_array | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| simple_divide | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_modulo | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_multiply | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_pointer | c2rust_only | 13 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_pointer_decrement | c2rust_only | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_pointer_double | c2rust_only | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_subtract | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_sum | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| string_length | c2rust_only | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| string_length_long | c2rust_only | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| string_length_size_t | c2rust_only | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| sum_diff_outputs | c2rust_only | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | None | None |
| unsupported_function_pointer | c2rust_only | 14 | 3 | 0.2 | 3 | 1 | 0 | 0.0 | None | None |
| unsupported_inline_asm | c2rust_only | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 | None | None |
| unsupported_union | c2rust_only | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 | None | None |
| unsupported_volatile | c2rust_only | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 | None | None |

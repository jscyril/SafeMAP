# SafeMAP Paper Tables

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

## Failure Categories

| Mode | Category | Count |
|---|---|---:|
| c2rust_only | unsupported | 5 |

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
| array_max | c2rust_only | 15 | 2 | 0.5 | 4 | 0 | 0 | 0.0 |  |  |
| array_total | c2rust_only | 13 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| boolean_greater_equal | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_int | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_less_equal | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_negative | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_nonzero | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| error_code | c2rust_only | 15 | 2 | 0.333 | 3 | 0 | 0 | 0.0 |  |  |
| error_code_product | c2rust_only | 14 | 2 | 0.333 | 3 | 0 | 0 | 0.0 |  |  |
| malloc_free | c2rust_only | 18 | 2 | 0.0 | 4 | 0 | 0 | 0.0 |  |  |
| malloc_free_constant | c2rust_only | 15 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| malloc_vec | c2rust_only | 20 | 2 | 0.0 | 5 | 0 | 0 | 0.0 |  |  |
| min_max_outputs | c2rust_only | 14 | 2 | 0.5 | 4 | 0 | 0 | 0.0 |  |  |
| multiple_outputs | c2rust_only | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| mutable_buffer | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_add_two | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_decrement | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_subtract_two | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| nullable_pointer | c2rust_only | 14 | 2 | 1.0 | 3 | 0 | 0 | 0.0 |  |  |
| nullable_pointer_zero | c2rust_only | 13 | 2 | 1.0 | 3 | 0 | 0 | 0.0 |  |  |
| output_double | c2rust_only | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| output_parameter | c2rust_only | 18 | 2 | 0.667 | 5 | 0 | 0 | 0.0 |  |  |
| output_square | c2rust_only | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| pointer_length_array | c2rust_only | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| simple_divide | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_modulo | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_multiply | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer | c2rust_only | 13 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer_decrement | c2rust_only | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer_double | c2rust_only | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_subtract | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_sum | c2rust_only | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length | c2rust_only | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_long | c2rust_only | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_size_t | c2rust_only | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| sum_diff_outputs | c2rust_only | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| unsupported_function_pointer | c2rust_only | 14 | 3 | 0.2 | 3 | 1 | 0 | 0.0 |  |  |
| unsupported_inline_asm | c2rust_only | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_union | c2rust_only | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 |  |  |
| unsupported_volatile | c2rust_only | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 |  |  |

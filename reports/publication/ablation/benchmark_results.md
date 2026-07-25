# SafeMAP Benchmark Summary

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| safemap_no_static_guidance | 40 | `no_guided_synthesis`: 40 | 0 | 76 | 0.000 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|
| safemap_no_static_guidance | 40 | 0 | 0.000 | `not_accepted`: 40 |

## Idiom Success

| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |
|---|---|---:|---:|---:|

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| safemap_no_static_guidance | 513 | 81 | 29 | 74 | 0.392 | 103 | 6 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| array_max | safemap_no_static_guidance | 15 | 2 | 0.5 | 4 | 0 | 0 | 0.0 | None | None |
| array_total | safemap_no_static_guidance | 13 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| boolean_greater_equal | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| boolean_int | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| boolean_less_equal | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| boolean_negative | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| boolean_nonzero | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| error_code | safemap_no_static_guidance | 15 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | None | None |
| error_code_product | safemap_no_static_guidance | 14 | 2 | 0.333 | 3 | 0 | 0 | 0.0 | None | None |
| malloc_free | safemap_no_static_guidance | 18 | 2 | 0.0 | 4 | 0 | 0 | 0.0 | None | None |
| malloc_free_constant | safemap_no_static_guidance | 15 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| malloc_vec | safemap_no_static_guidance | 20 | 2 | 0.0 | 5 | 0 | 0 | 0.0 | None | None |
| min_max_outputs | safemap_no_static_guidance | 14 | 2 | 0.5 | 4 | 0 | 0 | 0.0 | None | None |
| multiple_outputs | safemap_no_static_guidance | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | None | None |
| mutable_buffer | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| mutable_buffer_add_two | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| mutable_buffer_decrement | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| mutable_buffer_subtract_two | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| nullable_pointer | safemap_no_static_guidance | 14 | 2 | 1.0 | 3 | 0 | 0 | 0.0 | None | None |
| nullable_pointer_zero | safemap_no_static_guidance | 13 | 2 | 1.0 | 3 | 0 | 0 | 0.0 | None | None |
| output_double | safemap_no_static_guidance | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | None | None |
| output_parameter | safemap_no_static_guidance | 18 | 2 | 0.667 | 5 | 0 | 0 | 0.0 | None | None |
| output_square | safemap_no_static_guidance | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | None | None |
| pointer_length_array | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 | None | None |
| simple_divide | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_modulo | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_multiply | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_pointer | safemap_no_static_guidance | 13 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_pointer_decrement | safemap_no_static_guidance | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_pointer_double | safemap_no_static_guidance | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_subtract | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| simple_sum | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 | None | None |
| string_length | safemap_no_static_guidance | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| string_length_long | safemap_no_static_guidance | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| string_length_size_t | safemap_no_static_guidance | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 | None | None |
| sum_diff_outputs | safemap_no_static_guidance | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 | None | None |
| unsupported_function_pointer | safemap_no_static_guidance | 14 | 3 | 0.2 | 3 | 1 | 0 | 0.0 | None | None |
| unsupported_inline_asm | safemap_no_static_guidance | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 | None | None |
| unsupported_union | safemap_no_static_guidance | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 | None | None |
| unsupported_volatile | safemap_no_static_guidance | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 | None | None |

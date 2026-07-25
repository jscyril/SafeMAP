# SafeMAP Paper Tables

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

## Failure Categories

| Mode | Category | Count |
|---|---|---:|
| safemap_no_static_guidance | unsupported | 5 |

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
| array_max | safemap_no_static_guidance | 15 | 2 | 0.5 | 4 | 0 | 0 | 0.0 |  |  |
| array_total | safemap_no_static_guidance | 13 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| boolean_greater_equal | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_int | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_less_equal | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_negative | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| boolean_nonzero | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| error_code | safemap_no_static_guidance | 15 | 2 | 0.333 | 3 | 0 | 0 | 0.0 |  |  |
| error_code_product | safemap_no_static_guidance | 14 | 2 | 0.333 | 3 | 0 | 0 | 0.0 |  |  |
| malloc_free | safemap_no_static_guidance | 18 | 2 | 0.0 | 4 | 0 | 0 | 0.0 |  |  |
| malloc_free_constant | safemap_no_static_guidance | 15 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| malloc_vec | safemap_no_static_guidance | 20 | 2 | 0.0 | 5 | 0 | 0 | 0.0 |  |  |
| min_max_outputs | safemap_no_static_guidance | 14 | 2 | 0.5 | 4 | 0 | 0 | 0.0 |  |  |
| multiple_outputs | safemap_no_static_guidance | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| mutable_buffer | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_add_two | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_decrement | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| mutable_buffer_subtract_two | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| nullable_pointer | safemap_no_static_guidance | 14 | 2 | 1.0 | 3 | 0 | 0 | 0.0 |  |  |
| nullable_pointer_zero | safemap_no_static_guidance | 13 | 2 | 1.0 | 3 | 0 | 0 | 0.0 |  |  |
| output_double | safemap_no_static_guidance | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| output_parameter | safemap_no_static_guidance | 18 | 2 | 0.667 | 5 | 0 | 0 | 0.0 |  |  |
| output_square | safemap_no_static_guidance | 12 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| pointer_length_array | safemap_no_static_guidance | 14 | 2 | 0.5 | 3 | 0 | 0 | 0.0 |  |  |
| simple_divide | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_modulo | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_multiply | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer | safemap_no_static_guidance | 13 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer_decrement | safemap_no_static_guidance | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_pointer_double | safemap_no_static_guidance | 12 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_subtract | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| simple_sum | safemap_no_static_guidance | 10 | 2 | 0.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length | safemap_no_static_guidance | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_long | safemap_no_static_guidance | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| string_length_size_t | safemap_no_static_guidance | 11 | 2 | 1.0 | 2 | 0 | 0 | 0.0 |  |  |
| sum_diff_outputs | safemap_no_static_guidance | 14 | 2 | 0.5 | 2 | 0 | 0 | 0.0 |  |  |
| unsupported_function_pointer | safemap_no_static_guidance | 14 | 3 | 0.2 | 3 | 1 | 0 | 0.0 |  |  |
| unsupported_inline_asm | safemap_no_static_guidance | 11 | 2 | 0.0 | 2 | 2 | 0 | 0.0 |  |  |
| unsupported_union | safemap_no_static_guidance | 15 | 2 | 0.0 | 2 | 1 | 0 | 0.0 |  |  |
| unsupported_volatile | safemap_no_static_guidance | 12 | 2 | 1.0 | 2 | 2 | 0 | 0.0 |  |  |

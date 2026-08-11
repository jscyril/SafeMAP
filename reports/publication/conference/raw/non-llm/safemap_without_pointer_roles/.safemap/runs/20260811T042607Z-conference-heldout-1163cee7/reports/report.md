# SafeMAP Migration Report

## Project Summary

Project: `libcsv`

Total translation units: `23`

Eligible units: `17`

Fully safe accepted units: `0`

Fully safe translation unit acceptance rate: `0.0`

## Eligibility Classification

- `safe_translatable`: 6
- `safe_translatable_with_api_change`: 11
- `unsupported`: 6

## Baseline Results

Compilation: `None`

## SafeMAP Results

Compilation: `False`

SafeMAP accepts a unit only when the generated Rust compiles with `#![forbid(unsafe_code)]`, has no unsafe constructs, exposes no raw-pointer public API, and passes available validation.

## Comparison

| Metric | C2Rust Baseline | SafeMAP | Improvement |
|---|---:|---:|---:|
| Unsafe blocks | N/A | 0 | N/A |
| Unsafe functions | N/A | 0 | N/A |
| Raw pointer types | N/A | 0 | N/A |
| Raw pointer dereferences | N/A | 0 | N/A |
| Unsafe lines | N/A | 0 | N/A |

## Fully Safe Accepted Units

None.

## Migrated Idioms

- `error_code_return`: 3
- `nullable_pointer`: 5
- `struct_pointer`: 1

## Failure Categories

- `unsupported`: 6
- `validation_failed`: 5

## Remaining Unsafe Code

None.

## Validation Results

Test pass rate: `None`

Differential pass rate: `None`

## Failed Units

None.

## Recommendations for Manual Review

Review failed translation units and every residual unsafe classification.

# SafeMAP Migration Report

## Project Summary

Project: `inih`

Total translation units: `10`

Eligible units: `8`

Fully safe accepted units: `0`

Fully safe translation unit acceptance rate: `0.0`

## Eligibility Classification

- `safe_translatable`: 4
- `safe_translatable_with_api_change`: 4
- `unsafe_required`: 1
- `unsupported`: 1

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

- `pointer_length_array`: 2

## Failure Categories

- `unsafe_required`: 1
- `unsupported`: 1
- `validation_failed`: 1

## Remaining Unsafe Code

None.

## Validation Results

Test pass rate: `None`

Differential pass rate: `None`

## Failed Units

None.

## Recommendations for Manual Review

Review failed translation units and every residual unsafe classification.

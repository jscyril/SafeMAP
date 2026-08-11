# SafeMAP Migration Report

## Project Summary

Project: `cjson`

Total translation units: `109`

Eligible units: `57`

Fully safe accepted units: `0`

Fully safe translation unit acceptance rate: `0.0`

## Eligibility Classification

- `requires_manual_refactor`: 34
- `safe_translatable`: 16
- `safe_translatable_with_api_change`: 41
- `unsafe_required`: 7
- `unsupported`: 15

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
| Raw pointer dereferences | N/A | 8 | N/A |
| Unsafe lines | N/A | 0 | N/A |

## Fully Safe Accepted Units

None.

## Migrated Idioms

- `c_string`: 1
- `nullable_pointer`: 11

## Failure Categories

- `requires_manual_refactor`: 34
- `unsafe_required`: 7
- `unsupported`: 15
- `validation_failed`: 9

## Remaining Unsafe Code

None.

## Validation Results

Test pass rate: `None`

Differential pass rate: `None`

## Failed Units

None.

## Recommendations for Manual Review

Review failed translation units and every residual unsafe classification.

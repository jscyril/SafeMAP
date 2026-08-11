# SafeMAP Migration Report

## Project Summary

Project: `inih`

Total translation units: `10`

Eligible units: `1`

Fully safe accepted units: `0`

Fully safe translation unit acceptance rate: `0.0`

## Eligibility Classification

- `requires_manual_refactor`: 7
- `safe_translatable_with_api_change`: 1
- `unsafe_required`: 1
- `unsupported`: 1

## Baseline Results

Compilation: `None`

## SafeMAP Results

Compilation: `None`

SafeMAP accepts a unit only when the generated Rust compiles with `#![forbid(unsafe_code)]`, has no unsafe constructs, exposes no raw-pointer public API, and passes available validation.

## Comparison

| Metric | C2Rust Baseline | SafeMAP | Improvement |
|---|---:|---:|---:|
| Unsafe blocks | N/A | N/A | N/A |
| Unsafe functions | N/A | N/A | N/A |
| Raw pointer types | N/A | N/A | N/A |
| Raw pointer dereferences | N/A | N/A | N/A |
| Unsafe lines | N/A | N/A | N/A |

## Fully Safe Accepted Units

None.

## Migrated Idioms

None.

## Failure Categories

- `requires_manual_refactor`: 7
- `unsafe_required`: 1
- `unsupported`: 1

## Remaining Unsafe Code

None.

## Validation Results

Test pass rate: `None`

Differential pass rate: `None`

## Failed Units

None.

## Recommendations for Manual Review

Review failed translation units and every residual unsafe classification.

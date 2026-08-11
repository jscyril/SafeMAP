# SafeMAP Paper Tables

## Mode Summary

| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |
|---|---:|---|---:|---:|---:|
| llm_only | 3 | `completed`: 1, `no_final_output`: 2 | 0 | 70 | 0.000 |

## Declared Target Summary

| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |
|---|---:|---:|---:|---|

## Idiom Success

| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |
|---|---|---:|---:|---:|

## Failure Categories

| Mode | Category | Count |
|---|---|---:|
| llm_only | requires_manual_refactor | 46 |
| llm_only | unsafe_required | 8 |
| llm_only | unsupported | 22 |

## Validation Statuses

| Mode | Check | Status | Count |
|---|---|---|---:|
| llm_only | c_sanitizers | unsupported | 1 |
| llm_only | cargo_check | failed | 1 |
| llm_only | cargo_test | failed | 1 |
| llm_only | clippy | failed | 1 |
| llm_only | differential | failed | 1 |
| llm_only | miri | skipped | 1 |

## Dataset Characterization

| Mode | C LOC | Functions | Pointer Parameters | Parameters | Pointer Density | Complexity | Unsupported Constructs |
|---|---:|---:|---:|---:|---:|---:|---:|
| llm_only | 4062 | 146 | 229 | 282 | 0.812 | 851 | 22 |

## Project Results

| Project | Mode | C LOC | Functions | Pointer Density | Complexity | Unsupported | Accepted | Acceptance Rate | Differential | Miri |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| cjson | llm_only | 3191 | 113 | 0.827 | 632 | 15 | 0 | 0.0 |  |  |
| inih | llm_only | 326 | 10 | 0.893 | 87 | 1 | 0 | 0.0 | failed | skipped |
| libcsv | llm_only | 545 | 23 | 0.712 | 132 | 6 | 0 | 0.0 |  |  |

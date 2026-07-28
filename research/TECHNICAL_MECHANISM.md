# SafeMAP Technical Mechanism

This document is the source for the paper's worked example and algorithm
listing. The example is from the previously observed LLVM development corpus;
it is not held-out evidence.

## Worked accepted example

### 1. Original C

From `fp_convert/fp-convert.c`:

```c
double loop(float *x, float *y, long length) {
  long i;
  double accumulator = 0.0;
  for (i = 0; i < length; ++i) {
    accumulator += (double)x[i] * (double)y[i];
  }
  return accumulator;
}
```

### 2. Extracted facts

```text
analysis_backend = libclang
x: float*, indexed, paired with length, never written
   role = pointer_length_array, confidence = 0.94
y: float*, indexed, paired with length, never written
   role = pointer_length_array, confidence = 0.94
calls = []
dependency successors = []
```

The write analysis is syntactic and explicit: an indexed pointer is mutable
only if the indexed expression is the target of an assignment, compound
assignment, increment, or decrement. Merely reading `x[i]` or `y[i]` does not
create a mutable-alias conflict.

### 3. Candidate and support decisions

```text
candidate_decision = candidate_safe
legacy_eligibility = safe_translatable_with_api_change
synthesis_support = implemented_support
synthesis_rule = slice_dot_product
```

`candidate_safe` means that the screening analysis found no known obstacle. It
is not a proof of translatability. `implemented_support` is a separate statement that
the frozen synthesizer has an exact matching rule.

### 4. Migration-plan representation

```json
{
  "function": "loop",
  "candidate_decision": "candidate_safe",
  "analysis_backend": "libclang",
  "target_signature": "pub fn r#loop(x: &[f32], y: &[f32]) -> f64",
  "patterns": [
    {
      "pattern": "pointer_length_array",
      "replacement": "Use &[T] or &mut [T]",
      "confidence": 0.94
    }
  ],
  "synthesis_support": "implemented_support",
  "synthesis_rule": "slice_dot_product",
  "constraints": [
    "Preserve observable C behavior",
    "Do not use unsafe code",
    "Do not expose raw pointer public APIs",
    "Compile with #![forbid(unsafe_code)]"
  ]
}
```

The raw identifier `r#loop` is required because `loop` is a Rust keyword.

### 5. Generated Rust

```rust
#![forbid(unsafe_code)]

pub fn r#loop(x: &[f32], y: &[f32]) -> f64 {
    x.iter()
        .zip(y.iter())
        .map(|(&left, &right)| (left as f64) * (right as f64))
        .fold(0.0_f64, |accumulator, value| accumulator + value)
}
```

The length parameter is consumed by the two slice lengths. The generated
function evaluates pairs in input order and performs the multiplication and
accumulation in `f64`, matching the explicit C casts. The explicit positive-zero
fold also preserves C's result for an empty input; Rust's generic floating
`sum()` uses negative zero as its identity and failed exact differential
testing for that case.

### 6. Validation

The development check used a generated signature-driven harness:

```text
generator = lcg32-small-scalars-v1
seed = 0
cases = 1000 in the final development run
C output encoding = exact IEEE-754 f64 bits
Rust output encoding = exact IEEE-754 f64 bits
differential status = passed
cargo check = passed
cargo test = passed
clippy = passed
ASan + UBSan on C harness = passed
policy-safe = yes
behaviorally validated policy-safe = yes
```

The frozen evaluation uses the configured conference case count and records
every concrete input and output. This development run is not a final conference
result.

## Rejection contrast

The development function `doTest` in `lowercase.c` allocates buffers and invokes
`memcpy` and `memset`. The current classifier records:

```text
candidate_decision = unsafe_required
synthesis_support = not_applicable
generated = false
reason = depends on operations that normally require unsafe Rust or FFI
```

This is a conservative screening rejection. A human can redesign ownership and
replace the operations with safe slices, but the frozen automatic pipeline does
not claim that transformation.

## Algorithm

```text
ANALYZE(project):
  parse each translation unit with libclang
  if libclang fails:
    parse with the regex fallback and record the failure reason
  for each function:
    extract signature, body, calls, source range
    classify pointer roles with evidence and confidence
    detect migration idioms
  return facts with analysis-backend provenance

CLASSIFY_CANDIDATE(function):
  if union, function pointer, inline assembly, volatile access,
     setjmp/longjmp, or pointer-integer cast is detected:
    return unknown
  if an operation currently requires unsafe Rust or FFI:
    return unsafe_required
  if a pointer role or mutable-alias relation is unresolved:
    return manual_refactor_required
  return candidate_safe

BUILD_UNITS(functions):
  construct the internal call graph
  collapse strongly connected components
  topologically order components
  record cross-unit dependencies

PLAN(function, unit, candidate):
  derive a Rust-native signature from pointer roles
  attach idiom transformations above the confidence threshold
  attach safety constraints and validation obligations
  if candidate is not candidate_safe:
    mark synthesis support not_applicable
  else:
    select an exact synthesis rule
    mark implemented_support only if one rule matches

SELECT_RULE(function, plan):
  test non-overlapping predicates in a fixed order
  examples: bit reverse, Boolean integer, scalar expression,
            allocation, output tuple, slice update, dot product,
            reduction, and slice maximum
  return the first exact rule, otherwise not_implemented

VALIDATE(generated crate, original C):
  cargo check
  cargo test
  clippy
  miri when applicable
  generate deterministic C and Rust differential harnesses
  run bounded/random cases with a recorded seed
  run the C oracle with ASan and UBSan
  apply the no-unsafe/no-raw-public-pointer policy
  report policy-safe and behaviorally validated policy-safe separately
```

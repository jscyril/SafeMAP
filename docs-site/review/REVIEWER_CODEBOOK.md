# SafeMAP Held-Out Eligibility Review Codebook

Version: `safemap.eligibility_codebook.v1`

## Review question

For each C function, answer:

> Based only on the pinned C source and this codebook, can an automatic tool
> plausibly translate the function to Rust whose implementation uses no unsafe
> Rust, contains no `extern "C"` block, and exposes no raw-pointer public API,
> while preserving the function's intended observable behavior under a
> reasonable Rust-native API redesign?

Do not judge whether SafeMAP, C2Rust, an LLM, or any named tool can perform the
translation today. Do not reward or penalize a function because its pattern
looks easy to implement in a particular tool.

## Labels

### `candidate_safe`

Use when no source-level obstacle is visible and a routine, local Rust-native
representation appears sufficient. Typical examples include:

- scalar arithmetic and branching;
- read-only pointer plus length that can become `&[T]`;
- exclusive mutable pointer plus length that can become `&mut [T]`;
- nullable borrowed input that can become `Option<&T>`;
- output parameters that can become return values or tuples;
- return-code-plus-output conventions that can become `Result<T, E>`;
- ownership with a single clear allocator/deallocator path that can become
  `Box<T>`, `Vec<T>`, or another standard safe owner;
- internal calls whose callees can use compatible safe APIs.

The label means "no known obstacle after careful screening." It is not a proof
of semantic equivalence.

### `manual_refactor_required`

Use when safe Rust appears feasible but choosing the correct ownership, API, or
architecture requires human judgment or non-local redesign. Typical reasons:

- aliasing or lifetime relationships cannot be recovered locally;
- a pointer may be borrowed, owned, interior, shared, or nullable depending on
  undocumented caller behavior;
- global or stateful APIs require redesign across multiple functions;
- callbacks can be modeled safely only after selecting an application-specific
  trait, closure, or ownership boundary;
- error handling, allocation, or mutation semantics require a policy choice;
- macro expansion or build configuration hides behavior needed for a safe API;
- safe translation is possible, but not as a routine mechanical local mapping.

### `unsafe_required`

Use only when preserving the function's intended behavior genuinely appears to
require operations outside safe Rust at the relevant boundary. Examples can
include:

- volatile device or memory-mapped I/O;
- inline assembly;
- foreign-function calls that must remain at the translated boundary;
- pointer/integer address manipulation with observable address semantics;
- dependence on a C ABI or layout that cannot be isolated behind an already
  safe abstraction;
- deliberate access outside Rust's safe reference and slice rules.

Do not use this label merely because the C source uses pointers, `malloc`,
unions, callbacks, or casts. Many such cases can instead be
`manual_refactor_required` or, when the ownership is clear, `candidate_safe`.

### `unknown`

Use when the available evidence is insufficient or contradictory. Examples:

- essential declarations, macro definitions, generated headers, or callees are
  missing;
- intended behavior depends on undocumented undefined behavior;
- the function is truncated or cannot be parsed confidently;
- two labels remain equally plausible after applying the decision tree.

`unknown` is not a convenient substitute for a difficult decision. State
exactly which missing fact prevents a label.

## Decision tree

Apply these questions in order:

1. **Is the evidence sufficient?** If essential context is missing, choose
   `unknown` and identify it.
2. **Does intended behavior inherently require unsafe operations or an exposed
   foreign/raw boundary?** If yes, choose `unsafe_required`.
3. **Can ownership, lifetimes, aliasing, and API shape be selected by a routine
   local rule?** If no, but safe Rust still seems feasible, choose
   `manual_refactor_required`.
4. **Otherwise**, choose `candidate_safe`.

When uncertain between adjacent labels, choose the more conservative label and
record the uncertainty. Do not infer undocumented preconditions merely to make
a function eligible.

## Unit and context rules

- Label the named function, but inspect its type declarations, macros, globals,
  direct callees, and documented callers when needed.
- Assume that ordinary Rust-native API changes are allowed. Exact C ABI
  preservation is not required unless it is part of the function's intended
  externally visible behavior.
- Do not assume that an entire library has already been translated.
- A safe wrapper around an unavoidable unsafe dependency does not make the
  implementation itself safe under this study's policy.
- C undefined behavior is not behavior that the Rust translation must preserve.
  If intended defined behavior cannot be separated from possible undefined
  behavior, use `unknown` and explain why.
- Performance differences alone do not determine eligibility unless they are
  part of observable real-time or hardware behavior.

## Confidence

Use the following five-point scale:

1. **Very low:** a tentative label; essential context may be missing.
2. **Low:** plausible, but another label has substantial support.
3. **Moderate:** the main evidence supports the label with identifiable doubt.
4. **High:** strong source evidence with only minor uncertainty.
5. **Very high:** direct and unambiguous source evidence.

Confidence is not a substitute for rationale. Low-confidence responses remain
valid and are especially useful during adjudication.

## Construct tags

Select all that materially influenced the judgment. The generated form offers
these normalized tags:

- `aliasing`
- `allocation`
- `array_or_slice`
- `callback_or_function_pointer`
- `c_string`
- `custom_allocator`
- `error_code`
- `extern_or_ffi`
- `global_state`
- `inline_assembly`
- `macro_or_conditional_compilation`
- `nullable_pointer`
- `output_parameter`
- `pointer_arithmetic`
- `pointer_integer_cast`
- `recursive_or_cyclic_call`
- `setjmp_longjmp`
- `shared_mutability`
- `struct_or_union`
- `threading_or_synchronization`
- `unknown_pointer_ownership`
- `volatile_access`
- `other`

Do not select a tag merely because the syntax occurs. Select it when it affects
the eligibility decision or confidence.

## Rationale standard

Write two to six specific sentences. A useful rationale names:

1. the source evidence;
2. the likely safe Rust representation or the blocking issue;
3. any assumption or missing context; and
4. why the chosen label is preferable to the nearest alternative.

Weak: "Uses pointers, so it needs manual work."

Strong: "`data` and `length` are passed separately, but the function stores
`data` in global parser state that outlives the call. The caller's ownership
contract is not documented in the pinned headers. Safe Rust appears possible,
but choosing an owner and lifetime requires a library-level API redesign, so I
label it `manual_refactor_required` rather than `candidate_safe`."

## Independence and prohibited information

During independent review, do not inspect:

- SafeMAP analysis or migration plans;
- generated Rust;
- compiler, sanitizer, differential, or baseline results;
- another reviewer's labels;
- discussions that reveal how a specific function was classified.

The upstream project documentation and pinned source history may be consulted
when necessary, but record any external material that materially affects a
label.

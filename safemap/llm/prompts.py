REWRITE_SYSTEM_PROMPT = (
    "You rewrite C code or C2Rust reference output into fully safe, idiomatic Rust. "
    "Preserve behavior and return exactly one complete Rust function. Never use unsafe."
)

REWRITE_TEMPLATE = """You are rewriting Rust code generated from C.

Rules:
1. Do not use unsafe, unsafe fn, unsafe impl, extern "C", *const, or *mut.
2. Preserve observable behavior.
3. Use the target signature exactly.
4. Do not invent external crates.
5. Return one complete function and no prose or Markdown fences.
6. Do not use todo!(), unimplemented!(), placeholder code, or panic!() unless the C behavior genuinely aborts.
7. Do not silently drop behavior.

Original C code:
<<<C_CODE>>>

Current Rust code:
<<<RUST_CODE>>>

Static analysis facts:
<<<ANALYSIS_FACTS>>>

Migration plan:
<<<MIGRATION_PLAN>>>

Target Rust signature:
<<<TARGET_SIGNATURE>>>

Existing tests:
<<<TESTS>>>

Compiler errors from previous attempt:
<<<COMPILER_ERRORS>>>
"""

REPAIR_TEMPLATE = """The Rust function below failed to compile.

Fix the compiler errors while preserving the migration plan and target signature.
Do not use unsafe, unsafe fn, unsafe impl, extern "C", *const, or *mut.
Do not use todo!(), unimplemented!(), placeholder code, or panic!() unless the C behavior genuinely aborts.
Return one complete function with no prose.

Original C code:
<<<C_CODE>>>

Current Rust code:
<<<CURRENT_RUST_CODE>>>

Migration plan:
<<<MIGRATION_PLAN>>>

Compiler errors:
<<<COMPILER_ERRORS>>>
"""

SYNTHESIS_SYSTEM_PROMPT = (
    "You translate one C function into one safe Rust function with identical "
    "observable behavior. You never use unsafe code. You reply with Rust code only."
)

SYNTHESIS_TEMPLATE = """Translate this C function into safe Rust.

Hard requirements:
1. Use exactly this signature (same names, types, and parameter order):
   <<<TARGET_SIGNATURE>>>
2. Preserve observable behavior for every input on which the C code is defined:
   the return value and every value written through a mutable parameter.
   Mirror C integer semantics exactly (use wrapping_* where C unsigned
   arithmetic wraps; keep the same integer widths; C `char` values are bytes).
3. A `&str` / `Option<&str>` parameter is the C string up to (not including)
   its NUL terminator; `None` is NULL. A `&[u8]`/`&mut [u8]` parameter is the
   whole C buffer, and its length replaces the C length parameter. A returned
   `Option<String>` is the returned C string (None for NULL). A returned
   `Result<T, i32>` is `Err(code)` when C returns a nonzero error code and
   `Ok(...)` otherwise.
4. No `unsafe`, no raw pointers, no `extern`, no FFI, no external crates, no
   `todo!`/`unimplemented!`, and no panics on inputs where C is defined.
5. Declare any constants, lookup tables, or helper functions INSIDE the
   function body. Only the Rust types and functions listed below exist outside it.
6. Reply with exactly one Rust function and nothing else (no prose, no
   Markdown fences, no `use` lines outside the function).

C function:
<<<C_FUNCTION>>>

C definitions it references (macros, enums, constant tables):
<<<C_CONTEXT>>>

Rust types already defined in the crate:
<<<RUST_TYPES>>>

Already-translated Rust functions you may call:
<<<RUST_CALLEES>>>

Static analysis facts:
<<<ANALYSIS_FACTS>>>

Migration plan:
<<<MIGRATION_PLAN>>>
"""

SYNTHESIS_REPAIR_TEMPLATE = """Your previous answer was rejected. Fix it.

<<<ORIGINAL_PROMPT>>>

Your previous answer:
<<<PREVIOUS_RUST>>>

Rejection reason (compiler errors or policy violations):
<<<ERRORS>>>

Reply with the corrected single Rust function only.
"""

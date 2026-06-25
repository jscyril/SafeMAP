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

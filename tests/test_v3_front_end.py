"""v3 front-end rules: casts, globals, field-access and passed-pointer roles."""
from pathlib import Path

from safemap.analysis.c_analyzer import analyze_c_project, mark_written_globals
from safemap.analysis.eligibility import classify_function
from safemap.analysis.pointer_classifier import classify_pointers, resolve_passed_pointers
from safemap.models import CAnalysis, FunctionInfo, GlobalInfo, ParameterInfo, ProjectInfo


def _function(name, params, body, return_type="int"):
    function = FunctionInfo(name, return_type, params, body, "x.c", 1, 1)
    function.pointer_facts = classify_pointers(params, body)
    return function


def test_integer_cast_of_integer_is_not_a_pointer_cast() -> None:
    function = _function(
        "pad", [ParameterInfo("n", "int")],
        "int pad(int n) { size_t w = (size_t)n; return (int)w + (int)sizeof(int); }",
    )
    assert classify_function(function, "u").unsupported_features == []


def test_integer_cast_of_pointer_is_unsupported() -> None:
    param = ParameterInfo("p", "const char *", True, True)
    function = _function("addr", [param], "long addr(const char *p) { return (long)p; }")
    assert "pointer_integer_cast" in classify_function(function, "u").unsupported_features
    local = _function(
        "addr2", [], "long addr2(void) { char *q = 0; return (long)q; }",
    )
    assert "pointer_integer_cast" in classify_function(local, "u").unsupported_features


def test_memcpy_no_longer_forces_unsafe() -> None:
    function = _function(
        "copy", [ParameterInfo("n", "int")], "int copy(int n) { memset(buf, 0, n); return n; }",
    )
    function.calls = ["memset"]
    assert classify_function(function, "u").category != "unsafe_required"


def test_global_never_written_is_not_mutable_state() -> None:
    reader = _function("get", [], "int get(void) { return table[2] + limit; }")
    writer = _function("bump", [], "void bump(void) { counter++; }", "void")
    analysis = CAnalysis(functions=[reader, writer], globals=[
        GlobalInfo("table", "int[4]", True, "x.c", 1),
        GlobalInfo("limit", "int", True, "x.c", 2),
        GlobalInfo("counter", "int", True, "x.c", 3),
    ])
    mark_written_globals(analysis)
    assert {item.name: item.written for item in analysis.globals} == {
        "table": False, "limit": False, "counter": True,
    }


def test_global_array_passed_to_call_counts_as_written() -> None:
    caller = _function("fill", [], "void fill(void) { init(table, 4); }", "void")
    analysis = CAnalysis(functions=[caller], globals=[
        GlobalInfo("table", "int[4]", True, "x.c", 1),
    ])
    mark_written_globals(analysis)
    assert analysis.globals[0].written is True


def test_struct_handle_roles_from_field_access() -> None:
    reader = ParameterInfo("t", "struct tar *", True, False)
    facts = classify_pointers([reader], "int pos(struct tar *t) { return t->pos; }")
    assert facts[0].usage_kind == "input_borrow"
    facts = classify_pointers([reader], "void seek(struct tar *t) { t->pos = 0; }")
    assert facts[0].usage_kind == "mutable_borrow"
    # Stored or returned handles stay unresolved.
    facts = classify_pointers([reader], "struct tar *id(struct tar *t) { return t; }")
    assert facts[0].usage_kind == "unknown_raw_pointer"


def test_passed_pointer_takes_callee_role() -> None:
    param = ParameterInfo("t", "struct tar *", True, False)
    leaf = _function("leaf", [param], "void leaf(struct tar *t) { t->pos = 1; }", "void")
    mid = _function("mid", [param], "void mid(struct tar *t) { leaf(t); }", "void")
    top = _function("top", [param], "int top(struct tar *t) { mid(t); return t->pos; }")
    escape = _function("esc", [param], "void esc(struct tar *t) { keep(t); }", "void")
    resolve_passed_pointers([top, mid, leaf, escape])
    assert mid.pointer_facts[0].usage_kind == "mutable_borrow"
    assert top.pointer_facts[0].usage_kind == "mutable_borrow"
    # `keep` is unknown (not in the project, not a read-only libc call).
    assert escape.pointer_facts[0].usage_kind == "unknown_raw_pointer"


def test_const_string_passed_to_strlen_is_a_borrow() -> None:
    param = ParameterInfo("s", "const char *", True, True)
    function = _function("n", [param], "int n(const char *s) { return strlen(s) + foo(s); }")
    function.pointer_facts[0].usage_kind = "unknown_raw_pointer"
    resolve_passed_pointers([function])
    assert function.pointer_facts[0].usage_kind == "unknown_raw_pointer"
    function = _function("n", [param], "int n(const char *s) { return strlen(s); }")
    function.pointer_facts[0].usage_kind = "unknown_raw_pointer"
    resolve_passed_pointers([function])
    assert function.pointer_facts[0].usage_kind == "input_borrow"


def test_libclang_handles_typedef_array_parameter(tmp_path: Path) -> None:
    source = tmp_path / "v.c"
    source.write_text(
        "#include <stdarg.h>\n"
        "int first(va_list ap) { return 0; }\n"
        "int twice(int x) { return x * 2; }\n",
        encoding="utf-8",
    )
    project = ProjectInfo(root=str(tmp_path), c_files=[str(source)])
    analysis = analyze_c_project(project)
    assert analysis.analysis_backend == "libclang"
    assert {item.name for item in analysis.functions} == {"first", "twice"}


def test_crlf_source_bodies_match_their_functions(tmp_path: Path) -> None:
    source = tmp_path / "w.c"
    source.write_bytes(
        b"int one(void)\r\n{\r\n  return 1;\r\n}\r\n"
        b"int two(int x)\r\n{\r\n  return x + 2;\r\n}\r\n"
    )
    analysis = analyze_c_project(ProjectInfo(root=str(tmp_path), c_files=[str(source)]))
    bodies = {item.name: item.body for item in analysis.functions}
    assert bodies["two"].startswith("int two(int x)\n{")
    assert "return x + 2;" in bodies["two"]


def test_allocator_hooks_and_const_tables_are_not_mutable_state(tmp_path: Path) -> None:
    source = tmp_path / "h.c"
    source.write_text(
        "#include <stdlib.h>\n"
        "typedef void *(*Malloc_Fn)(size_t);\n"
        "static Malloc_Fn hook = malloc;\n"
        "static const int table[] = {1, 2, 3};\n"
        "void set_hook(Malloc_Fn f) { hook = f; }\n"
        "int third(void) { return table[2]; }\n"
        "int alloc_ok(void) { int *p = hook(4); int ok = p != 0; free(p); return ok; }\n",
        encoding="utf-8",
    )
    analysis = analyze_c_project(ProjectInfo(root=str(tmp_path), c_files=[str(source)]))
    globals_ = {item.name: item for item in analysis.globals}
    assert globals_["hook"].allocator_hook == "malloc"
    assert globals_["table"].mutable is False
    from safemap.analysis.eligibility import classify_analysis
    reasons = {item.function: item.reasons[0] for item in classify_analysis(analysis)}
    assert "global" not in reasons["third"]
    assert "global" not in reasons["alloc_ok"]
    # The setter still writes the hook.
    assert "global" in reasons["set_hook"]


def test_scanned_const_string_is_a_string_cursor() -> None:
    param = ParameterInfo("s", "const char *", True, True)
    scan = "int count(const char *s) { int n = 0; while (*s) { if (*s == 'a') n++; s++; } return n; }"
    assert classify_pointers([param], scan)[0].usage_kind == "c_string_cursor"
    indexed = "int first(const char *s) { return s[0] == 'x'; }"
    assert classify_pointers([param], indexed)[0].usage_kind == "c_string_cursor"
    # The pointer itself escapes: returned, or stored through an output.
    returned = "const char *skip(const char *s) { while (*s == ' ') s++; return s; }"
    assert classify_pointers([param], returned)[0].usage_kind != "c_string_cursor"
    out = ParameterInfo("end", "const char **", True, False)
    stored = "void scan(const char *s, const char **end) { s++; *end = s; }"
    assert classify_pointers([param, out], stored)[0].usage_kind != "c_string_cursor"
    # Mutable strings have no planned safe type.
    mutable = ParameterInfo("s", "char *", True, False)
    assert classify_pointers([mutable], "int f(char *s) { return s[1]; }")[0].usage_kind != "c_string_cursor"


def test_byte_buffers_are_not_string_cursors() -> None:
    key = ParameterInfo("key", "const unsigned char *", True, True)
    body = "void f(const unsigned char *key) { x ^= key[i * 4 + 1]; }"
    assert classify_pointers([key], body)[0].usage_kind != "c_string_cursor"


def test_pointer_to_array_role() -> None:
    grid = ParameterInfo("state", "unsigned char (*)[4][4]", True, False)
    used = "void f(unsigned char (*state)[4][4]) { (*state)[0][1] = 2; g(state); }"
    assert classify_pointers([grid], used)[0].usage_kind == "array_reference"
    escapes = "void *f(unsigned char (*state)[4][4]) { return state; }"
    assert classify_pointers([grid], escapes)[0].usage_kind == "unknown_raw_pointer"


def test_ctype_predicate_return_is_boolean() -> None:
    from safemap.analysis.idiom_detector import detect_idioms
    function = _function("matchalpha", [ParameterInfo("c", "char")],
                         "static int matchalpha(char c) { return isalpha(c); }")
    assert "boolean_int" in {item.idiom_type for item in detect_idioms(function)}
    count = _function("count", [ParameterInfo("c", "char")],
                      "static int count(char c) { return isalpha(c) + 1; }")
    assert "boolean_int" not in {item.idiom_type for item in detect_idioms(count)}

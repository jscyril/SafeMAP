import json
from types import SimpleNamespace

from safemap.config import SafeMapConfig
from safemap.models import CommandResult, ValidationCheck
from safemap.pipeline import _clippy_decision
from safemap.validation.clippy_runner import clippy_error_lines, function_spans

SOURCE = '''#![forbid(unsafe_code)]
pub fn e() -> f64 {
    2.71828182845904523536
}

// fn commented() {
pub fn braces(s: &str) -> usize {
    let t = "}{ \\" }";
    let c = '}';
    let r = r#"{"#;
    s.len() + t.len() + r.len() + (c as usize)
}

pub fn calls_e<'a>(x: &'a str) -> f64 {
    e() + x.len() as f64
}

const PI: f64 = 3.14159;
'''


def _message(level, line, text="lint"):
    span = {"file_name": "src/lib.rs", "line_start": line, "is_primary": True, "expansion": None}
    return json.dumps({"reason": "compiler-message", "message": {
        "level": level, "message": text, "spans": [span] if line else []}})


def _validation(*lines):
    stdout = "\n".join(lines)
    command = CommandResult(command=["cargo", "clippy"], cwd=".", exit_code=101, stdout=stdout, status="failed")
    return SimpleNamespace(clippy=ValidationCheck(status="failed", command=command))


def test_function_spans_skip_strings_chars_and_comments():
    assert function_spans(SOURCE) == [("e", 2, 4), ("braces", 7, 12), ("calls_e", 14, 16)]


def test_error_lines_ignore_warnings_and_summary():
    check = _validation(_message("warning", 3), _message("error", 3),
                        _message("error", None, "aborting due to 1 previous error")).clippy
    assert clippy_error_lines(check) == [("src/lib.rs", 3)]


def _decide(tmp_path, *lines, per_unit=True):
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src/lib.rs").write_text(SOURCE)
    config = SafeMapConfig()
    config.validation.per_unit_clippy = per_unit
    units = {"u_e": {"e"}, "u_braces": {"braces"}, "u_calls": {"calls_e"}}
    deps = {"u_e": [], "u_braces": [], "u_calls": ["u_e"]}
    return _clippy_decision(_validation(*lines), tmp_path, config, units, deps)


def test_error_in_unit_rejects_it_and_its_callers(tmp_path):
    assert _decide(tmp_path, _message("error", 3)) == (True, {"u_e", "u_calls"})


def test_error_outside_any_unit_fails_crate(tmp_path):
    assert _decide(tmp_path, _message("error", 18)) == (False, set())


def test_flag_off_keeps_crate_level_behavior(tmp_path):
    assert _decide(tmp_path, _message("error", 3), per_unit=False) == (False, set())

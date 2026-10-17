from pathlib import Path

from safemap.translation import c2rust_runner
from safemap.translation.c2rust_runner import _c2rust_environment, ensure_cargo_project


def test_single_c2rust_module_becomes_crate_root(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "cJSON.rs").write_text("pub fn f() {}\n", encoding="utf-8")

    ensure_cargo_project(tmp_path, "cjson")

    assert (src / "lib.rs").read_text(encoding="utf-8") == "pub fn f() {}\n"
    assert not (src / "cJSON.rs").exists()
    assert 'name = "cjson"' in (tmp_path / "Cargo.toml").read_text()


def test_environment_does_not_shadow_system_headers(monkeypatch) -> None:
    monkeypatch.setenv("C_INCLUDE_PATH", "")
    monkeypatch.setattr(c2rust_runner, "_clang_builtin_include_dir", lambda: "/clang/include")

    env = _c2rust_environment()

    # Shim headers used to come first and hid FILE, memcpy, sprintf, ...
    assert env["C_INCLUDE_PATH"] == "/clang/include"

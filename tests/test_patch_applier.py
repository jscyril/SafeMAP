from pathlib import Path

from safemap.translation.patch_applier import replace_rust_function


def test_replaces_only_target_function(tmp_path: Path) -> None:
    path = tmp_path / "lib.rs"
    path.write_text("fn first() { println!(\"}\"); }\nfn second() -> i32 { 2 }\n")
    old = replace_rust_function(path, "first", "fn first() { }")
    assert 'println!("}")' in old
    assert path.read_text() == "fn first() { }\nfn second() -> i32 { 2 }\n"


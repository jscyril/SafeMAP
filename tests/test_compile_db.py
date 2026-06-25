from pathlib import Path

from safemap.ingestion import compile_db
from safemap.models import CommandResult


def test_single_file_compile_db_uses_matching_resource_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "main.c"
    source.write_text("int main(void) { return 0; }")
    fake_clang = tmp_path / "llvm" / "bin" / "clang"
    fake_clang.parent.mkdir(parents=True)
    fake_clang.write_text("")
    monkeypatch.setenv("SAFEMAP_C2RUST_CLANG", str(fake_clang))

    def fake_run(command, cwd, timeout=None):
        return CommandResult(
            command=list(command),
            cwd=str(cwd),
            exit_code=0,
            stdout="/tmp/resource-dir\n",
            status="passed",
        )

    monkeypatch.setattr(compile_db, "run_command", fake_run)

    database, _ = compile_db.prepare_compile_database(
        tmp_path, "single_file", [source], tmp_path / "compile_db"
    )

    text = database.read_text(encoding="utf-8")
    assert str(fake_clang) in text
    assert "-resource-dir" in text
    assert "/tmp/resource-dir" in text

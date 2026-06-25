from pathlib import Path

from safemap.ingestion.file_discovery import detect_build_system, discover_files


def test_discovers_sources_and_ignores_build(tmp_path: Path) -> None:
    (tmp_path / "main.c").write_text("int main(void) { return 0; }")
    (tmp_path / "api.h").write_text("int api(void);")
    (tmp_path / "Makefile").write_text("all:\n\tclang main.c")
    ignored = tmp_path / "target"
    ignored.mkdir()
    (ignored / "generated.c").write_text("")

    files = discover_files(tmp_path)

    assert [item.name for item in files["c_files"]] == ["main.c"]
    assert [item.name for item in files["header_files"]] == ["api.h"]
    assert detect_build_system(tmp_path, files["build_files"]) == "make"


def test_single_source_directory_is_single_file_build() -> None:
    root = Path("examples/output_parameter")
    files = discover_files(root)

    assert detect_build_system(root, files["build_files"], files["c_files"]) == "single_file"

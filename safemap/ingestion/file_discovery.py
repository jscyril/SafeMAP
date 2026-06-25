from __future__ import annotations

from pathlib import Path

IGNORED_DIRS = {
    ".git", ".safemap", ".venv", "build", "dist", "target",
    "node_modules", "__pycache__",
}
BUILD_NAMES = {
    "Makefile", "makefile", "CMakeLists.txt", "meson.build",
    "configure", "compile_commands.json",
}


def discover_files(root: Path) -> dict[str, list[Path]]:
    if root.is_file():
        files = [root.resolve()]
    else:
        files = sorted(
            (
                item.resolve()
                for item in root.rglob("*")
                if item.is_file()
                and not any(part in IGNORED_DIRS for part in item.relative_to(root).parts)
            ),
            key=str,
        )
    c_files = [item for item in files if item.suffix.lower() == ".c"]
    headers = [item for item in files if item.suffix.lower() in {".h", ".hpp"}]
    build_files = [item for item in files if item.name in BUILD_NAMES]
    tests = [
        item for item in files
        if "test" in item.stem.lower() or "tests" in item.parts
    ]
    return {
        "c_files": c_files,
        "header_files": headers,
        "build_files": build_files,
        "test_files": tests,
    }


def detect_build_system(
    input_path: Path,
    build_files: list[Path],
    c_files: list[Path] | None = None,
) -> str:
    if input_path.is_file() and input_path.suffix.lower() == ".c":
        return "single_file"
    names = {item.name for item in build_files}
    if "compile_commands.json" in names:
        return "compile_commands"
    if "CMakeLists.txt" in names:
        return "cmake"
    if names.intersection({"Makefile", "makefile"}):
        return "make"
    if input_path.is_dir() and c_files is not None and len(c_files) == 1:
        return "single_file"
    return "unknown"

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from ..models import CommandResult
from ..process import run_command


def find_compile_database(root: Path) -> Path | None:
    candidates = [root / "compile_commands.json", root / "build" / "compile_commands.json"]
    return next((item.resolve() for item in candidates if item.exists()), None)


def prepare_compile_database(
    root: Path,
    build_system: str,
    c_files: list[Path],
    output_dir: Path,
) -> tuple[Path | None, CommandResult | None]:
    existing = find_compile_database(root)
    if existing:
        return existing, None
    output_dir.mkdir(parents=True, exist_ok=True)
    if build_system == "single_file" and c_files:
        database = output_dir / "compile_commands.json"
        clang, extra_args = _single_file_clang_arguments()
        database.write_text(json.dumps([{
            "directory": str(root),
            "arguments": [clang, *extra_args, "-c", str(c_files[0])],
            "file": str(c_files[0]),
        }], indent=2) + "\n", encoding="utf-8")
        return database, None
    if build_system == "cmake":
        result = run_command(
            ["cmake", "-S", str(root), "-B", str(output_dir), "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"],
            cwd=root,
        )
        generated = output_dir / "compile_commands.json"
        return (generated if generated.exists() else None), result
    if build_system == "make" and shutil.which("bear"):
        result = run_command(
            ["bear", "--output", str(output_dir / "compile_commands.json"), "--", "make"],
            cwd=root,
        )
        generated = output_dir / "compile_commands.json"
        return (generated if generated.exists() else None), result
    return None, None


def _single_file_clang_arguments() -> tuple[str, list[str]]:
    clang = _preferred_clang()
    resource_dir = _clang_resource_dir(clang)
    args = ["-resource-dir", resource_dir] if resource_dir else []
    return clang, args


def _preferred_clang() -> str:
    explicit = os.getenv("SAFEMAP_C2RUST_CLANG") or os.getenv("CC")
    if explicit:
        return explicit
    llvm_config = os.getenv("LLVM_CONFIG_PATH")
    if llvm_config:
        candidate = Path(llvm_config).resolve().parent / "clang"
        if candidate.exists():
            return str(candidate)
    for candidate in (
        "/opt/llvm-14.0.6/bin/clang",
        "/usr/lib/llvm-14/bin/clang",
        "clang-14",
        "clang",
    ):
        resolved = shutil.which(candidate) if not Path(candidate).is_absolute() else candidate
        if resolved and Path(resolved).exists():
            return str(resolved)
    return "clang"


def _clang_resource_dir(clang: str) -> str | None:
    override = os.getenv("SAFEMAP_C2RUST_RESOURCE_DIR")
    if override:
        return override
    result = run_command([clang, "--print-resource-dir"], Path.cwd())
    if result.status == "passed":
        resource_dir = result.stdout.strip().splitlines()[0]
        if resource_dir:
            return resource_dir
    return None

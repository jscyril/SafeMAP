from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from ..artifacts import ArtifactStore
from ..models import CommandResult, ProjectInfo
from ..process import run_command


def run_c2rust(project: ProjectInfo, store: ArtifactStore) -> CommandResult:
    output = store.path("baseline/rust")
    output.mkdir(parents=True, exist_ok=True)
    if shutil.which("c2rust") is None:
        result = CommandResult(
            command=["c2rust", "transpile"],
            cwd=project.root,
            exit_code=None,
            status="unsupported",
            reason="C2Rust is not installed",
        )
        store.write_json("logs/c2rust.json", result)
        return result
    if not project.compile_commands:
        result = CommandResult(
            command=["c2rust", "transpile"],
            cwd=project.root,
            exit_code=None,
            status="failed",
            reason="C2Rust requires compile_commands.json",
        )
        store.write_json("logs/c2rust.json", result)
        return result
    result = run_command(
        [
            "c2rust", "transpile", project.compile_commands,
            "--output-dir", str(output),
        ],
        cwd=Path(project.root),
        timeout=600,
        env=_c2rust_environment(store),
    )
    result.reason = result.reason or _diagnose_c2rust_failure(result)
    store.write_json("logs/c2rust.json", result)
    if result.status == "passed":
        ensure_cargo_project(output, project.project_name)
        check = run_command(["cargo", "check", "--message-format=json"], output, timeout=600)
        check.reason = check.reason or _diagnose_c2rust_compile_failure(check)
        store.write_json("baseline/compile.json", check)
    return result


def _c2rust_environment(store: ArtifactStore) -> dict[str, str]:
    env = dict(os.environ)
    candidates = [
        os.getenv("SAFEMAP_C2RUST_LIB_DIR"),
        os.getenv("LIBCLANG_PATH"),
        "/opt/llvm-14.0.6/lib",
        "/usr/lib/llvm-14/lib",
    ]
    existing = env.get("LD_LIBRARY_PATH", "")
    paths = [
        item for item in candidates
        if item and Path(item).exists()
    ]
    if paths:
        env["LD_LIBRARY_PATH"] = ":".join([*paths, existing] if existing else paths)
    include_paths = [
        str(_write_c2rust_header_shims(store)),
        _clang_builtin_include_dir(),
        env.get("C_INCLUDE_PATH", ""),
    ]
    env["C_INCLUDE_PATH"] = ":".join(item for item in include_paths if item)
    return env


def _write_c2rust_header_shims(store: ArtifactStore) -> Path:
    shim_dir = store.path("baseline/c2rust_include")
    shim_dir.mkdir(parents=True, exist_ok=True)
    (shim_dir / "stdio.h").write_text(
        "int printf(const char *format, ...);\n",
        encoding="utf-8",
    )
    (shim_dir / "stdlib.h").write_text(
        "#include <stddef.h>\n"
        "void *malloc(size_t size);\n"
        "void *calloc(size_t count, size_t size);\n"
        "void *realloc(void *ptr, size_t size);\n"
        "void free(void *ptr);\n"
        "int atoi(const char *nptr);\n",
        encoding="utf-8",
    )
    (shim_dir / "string.h").write_text(
        "#include <stddef.h>\n"
        "size_t strlen(const char *s);\n"
        "int strcmp(const char *s1, const char *s2);\n"
        "char *strcpy(char *dest, const char *src);\n"
        "char *strncpy(char *dest, const char *src, size_t n);\n",
        encoding="utf-8",
    )
    return shim_dir


def _clang_builtin_include_dir() -> str | None:
    override = os.getenv("SAFEMAP_C2RUST_RESOURCE_DIR")
    if override:
        include = Path(override)
        if include.name != "include":
            include = include / "include"
        return str(include) if include.exists() else override
    for candidate in (
        Path("/opt/llvm-14.0.6/lib/clang/14.0.6/include"),
        Path("/usr/lib/llvm-14/lib/clang/14/include"),
    ):
        if candidate.exists():
            return str(candidate)
    return None


def ensure_cargo_project(output: Path, project_name: str) -> None:
    if (output / "Cargo.toml").exists():
        return
    rs_files = list(output.rglob("*.rs"))
    src = output / "src"
    src.mkdir(exist_ok=True)
    if rs_files and rs_files[0].parent != src:
        shutil.copy2(rs_files[0], src / "lib.rs")
    elif not rs_files:
        (src / "lib.rs").write_text("", encoding="utf-8")
    rust_text = "\n".join(
        file.read_text(encoding="utf-8", errors="replace")
        for file in output.rglob("*.rs")
    )
    dependencies = "libc = \"0.2\"\n" if "libc::" in rust_text else ""
    normalized = project_name.replace("-", "_")
    (output / "Cargo.toml").write_text(
        "[package]\n"
        f'name = "{normalized}"\n'
        'version = "0.1.0"\n'
        'edition = "2021"\n\n'
        f"[dependencies]\n{dependencies}",
        encoding="utf-8",
    )


def load_baseline_status(store: ArtifactStore) -> dict:
    path = store.path("baseline/compile.json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _diagnose_c2rust_failure(result: CommandResult) -> str | None:
    if result.status == "passed":
        return None
    output = (result.stdout + "\n" + result.stderr).lower()
    if "libclang" in output and ("not found" in output or "cannot open" in output):
        return (
            "C2Rust could not load libclang. Set SAFEMAP_C2RUST_LIB_DIR or "
            "LIBCLANG_PATH to the LLVM 14 library directory used by c2rust."
        )
    if "llvm" in output and ("version" in output or "mismatch" in output):
        return (
            "C2Rust reported an LLVM version mismatch. Use an LLVM/libclang version "
            "compatible with the installed c2rust binary, or set "
            "SAFEMAP_C2RUST_RESOURCE_DIR and SAFEMAP_C2RUST_LIB_DIR explicitly."
        )
    if "stddef.h" in output or "stdio.h" in output or "stdlib.h" in output:
        return (
            "C2Rust could not resolve standard C headers. Check the Clang resource "
            "directory and C_INCLUDE_PATH; SAFEMAP_C2RUST_RESOURCE_DIR can override "
            "the builtin include path."
        )
    if "compile_commands" in output:
        return (
            "C2Rust failed while reading compile_commands.json. Regenerate the "
            "compile database and verify that each source path exists."
        )
    return None


def _diagnose_c2rust_compile_failure(result: CommandResult) -> str | None:
    if result.status == "passed":
        return None
    output = (result.stdout + "\n" + result.stderr).lower()
    if "#![feature" in output or "may not be used on the stable release channel" in output:
        return (
            "Raw C2Rust output requires nightly Rust feature gates. This is counted "
            "as a baseline compile failure, not a SafeMAP failure."
        )
    if "unresolved import `libc`" in output or "use of unresolved module or unlinked crate `libc`" in output:
        return (
            "Raw C2Rust output references libc but the generated crate could not "
            "resolve it. Check baseline Cargo.toml dependency generation."
        )
    return None

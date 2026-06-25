from __future__ import annotations

import random
import tempfile
from pathlib import Path

from ..models import ValidationCheck
from ..process import run_command


def compare_executables(
    c_command: list[str],
    rust_command: list[str],
    cwd: Path,
    inputs: list[str] | None = None,
    random_inputs: int = 0,
    seed: int = 0,
    timeout: float = 30,
) -> ValidationCheck:
    corpus = list(inputs or [""])
    generator = random.Random(seed)
    corpus.extend(
        f"{generator.randint(-1000, 1000)}\n" for _ in range(random_inputs)
    )
    mismatches = []
    for test_input in corpus:
        c_result = _run_with_input(c_command, cwd, test_input, timeout)
        rust_result = _run_with_input(rust_command, cwd, test_input, timeout)
        if c_result != rust_result:
            mismatches.append({
                "input": test_input,
                "c": c_result,
                "rust": rust_result,
            })
    total = len(corpus)
    passed = total - len(mismatches)
    reason = None
    if mismatches:
        reason = f"{len(mismatches)} of {total} inputs differed; first={mismatches[0]!r}"
    return ValidationCheck(
        status="passed" if not mismatches else "failed",
        passed=passed,
        failed=len(mismatches),
        reason=reason,
    )


def build_and_compare_projects(
    c_source: Path,
    rust_root: Path,
    inputs: list[str] | None = None,
    seed: int = 0,
) -> ValidationCheck:
    with tempfile.TemporaryDirectory(prefix="safemap-diff-") as temporary:
        c_binary = Path(temporary) / "original"
        compile_c = run_command(
            ["clang", str(c_source), "-o", str(c_binary)],
            c_source.parent,
        )
        if compile_c.status != "passed":
            return ValidationCheck(
                status=compile_c.status, command=compile_c,
                reason="Could not compile original C program",
            )
        build_rust = run_command(["cargo", "build", "--quiet"], rust_root, timeout=600)
        if build_rust.status != "passed":
            return ValidationCheck(
                status=build_rust.status, command=build_rust,
                reason="Could not build translated Rust program",
            )
        package = _package_name(rust_root / "Cargo.toml")
        rust_binary = rust_root / "target" / "debug" / package
        if not rust_binary.exists():
            return ValidationCheck(
                status="not_applicable",
                reason="Translated project does not produce a comparable executable",
            )
        return compare_executables(
            [str(c_binary)], [str(rust_binary)], rust_root, inputs=inputs, seed=seed
        )


def _run_with_input(
    command: list[str], cwd: Path, stdin: str, timeout: float
) -> tuple[int | None, str, str]:
    import subprocess
    try:
        result = subprocess.run(
            command, cwd=cwd, input=stdin, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except (subprocess.TimeoutExpired, OSError) as error:
        return None, "", str(error)


def _package_name(cargo_toml: Path) -> str:
    import re
    text = cargo_toml.read_text(encoding="utf-8")
    match = re.search(r'(?m)^name\s*=\s*"([^"]+)"', text)
    return match.group(1).replace("-", "_") if match else ""

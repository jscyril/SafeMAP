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
    random_inputs: int = 0,
) -> ValidationCheck:
    with tempfile.TemporaryDirectory(prefix="safemap-diff-") as temporary:
        temporary_path = Path(temporary)
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
            harness = _build_library_harness(
                c_source, rust_root, package, temporary_path,
                random_inputs=random_inputs, seed=seed,
            )
            if harness is None:
                return ValidationCheck(
                    status="not_applicable",
                    reason="Translated project does not produce a comparable executable",
                )
            return compare_executables(
                harness.c_command, harness.rust_command, rust_root,
                inputs=inputs, seed=seed,
            )
        return compare_executables(
            [str(c_binary)], [str(rust_binary)], rust_root, inputs=inputs,
            random_inputs=random_inputs, seed=seed,
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


class _HarnessCommands:
    def __init__(self, c_command: list[str], rust_command: list[str]) -> None:
        self.c_command = c_command
        self.rust_command = rust_command


def _build_library_harness(
    c_source: Path,
    rust_root: Path,
    package: str,
    temporary: Path,
    random_inputs: int = 0,
    seed: int = 0,
) -> _HarnessCommands | None:
    project = c_source.parent.name
    cases = max(1, random_inputs)
    c_source_text = _c_library_harness_source(project, c_source, cases, seed)
    rust_source = _rust_library_harness_source(project, package, cases, seed)
    if c_source_text is None or rust_source is None:
        return None

    c_harness = temporary / "function_harness.c"
    c_binary = temporary / "function_harness"
    c_harness.write_text(c_source_text, encoding="utf-8")
    compile_c = run_command(["clang", str(c_harness), "-o", str(c_binary)], temporary)
    if compile_c.status != "passed":
        return None

    harness_root = rust_root / "target" / "safemap-differential-harness"
    src = harness_root / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "main.rs").write_text(rust_source, encoding="utf-8")
    (harness_root / "Cargo.toml").write_text(
        "[package]\n"
        'name = "safemap_differential_harness"\n'
        'version = "0.1.0"\n'
        'edition = "2021"\n\n'
        "[dependencies]\n"
        f'{package} = {{ path = "{rust_root.as_posix()}" }}\n',
        encoding="utf-8",
    )
    build_rust = run_command(["cargo", "build", "--quiet"], harness_root, timeout=600)
    if build_rust.status != "passed":
        return None
    rust_binary = harness_root / "target" / "debug" / "safemap_differential_harness"
    if not rust_binary.exists():
        return None
    return _HarnessCommands([str(c_binary)], [str(rust_binary)])


def _c_library_harness_source(
    project: str,
    c_source: Path,
    cases: int,
    seed: int,
) -> str | None:
    include = str(c_source.resolve()).replace("\\", "\\\\").replace('"', '\\"')
    prefix = (
        "#include <stdio.h>\n"
        "#include <stddef.h>\n"
        "#define main safemap_original_main\n"
        f'#include "{include}"\n'
        "#undef main\n\n"
        "static int next_case(unsigned int *state) {\n"
        "    *state = *state * 1103515245u + 12345u;\n"
        "    return (int)((*state >> 16) % 201u) - 100;\n"
        "}\n\n"
        "int main(void) {\n"
        f"    unsigned int state = {seed & 0xffffffff}u;\n"
    )
    suffix = "    return 0;\n}\n"
    bodies = {
        "simple_sum": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int a = next_case(&state);\n"
            "        int b = next_case(&state);\n"
            "        printf(\"%d\\n\", simple_sum(a, b));\n"
            "    }\n"
        ),
        "boolean_int": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        printf(\"%d\\n\", is_even(value));\n"
            "    }\n"
        ),
        "pointer_length_array": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int arr[8];\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        for (int j = 0; j < len; j++) arr[j] = next_case(&state);\n"
            "        printf(\"%d\\n\", sum_array(arr, len));\n"
            "    }\n"
        ),
        "mutable_buffer": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int arr[8];\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        for (int j = 0; j < len; j++) arr[j] = next_case(&state);\n"
            "        increment_all(arr, len);\n"
            "        for (int j = 0; j < len; j++) printf(j + 1 == len ? \"%d\\n\" : \"%d \", arr[j]);\n"
            "    }\n"
        ),
        "multiple_outputs": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int divisor = ((next_case(&state) + 100) % 19) + 1;\n"
            "        int quotient = 0;\n"
            "        int remainder = 0;\n"
            "        divmod_pair(value, divisor, &quotient, &remainder);\n"
            "        printf(\"%d %d\\n\", quotient, remainder);\n"
            "    }\n"
        ),
        "simple_pointer": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        increment(&value);\n"
            "        printf(\"%d\\n\", value);\n"
            "    }\n"
        ),
        "string_length": (
            "    const char *values[] = {\"\", \"a\", \"hello\", \"migration\", \"safe rust\", \"abcdefghi\"};\n"
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        const char *text = values[(next_case(&state) + 100) % 6];\n"
            "        printf(\"%d\\n\", string_length(text));\n"
            "    }\n"
        ),
        "output_parameter": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int arr[8];\n"
            "        int len = (next_case(&state) + 100) % 9;\n"
            "        for (int j = 0; j < len; j++) arr[j] = next_case(&state);\n"
            "        int out = 0;\n"
            "        int status = get_max(arr, len, &out);\n"
            "        printf(\"%d %d\\n\", status, out);\n"
            "    }\n"
        ),
        "nullable_pointer": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int use_null = (next_case(&state) + 100) % 2;\n"
            "        printf(\"%d\\n\", read_value(use_null ? NULL : &value));\n"
            "    }\n"
        ),
        "error_code": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int a = next_case(&state);\n"
            "        int b = next_case(&state) % 11;\n"
            "        int out = 0;\n"
            "        int status = divide(a, b, &out);\n"
            "        printf(\"%d %d\\n\", status, out);\n"
            "    }\n"
        ),
        "malloc_free": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int *out = make_value(value);\n"
            "        printf(\"%d\\n\", *out);\n"
            "        free(out);\n"
            "    }\n"
        ),
    }
    body = bodies.get(project)
    return prefix + body + suffix if body is not None else None


def _rust_library_harness_source(
    project: str,
    package: str,
    case_count: int,
    seed: int,
) -> str | None:
    prefix = (
        "fn next_case(state: &mut u32) -> i32 {\n"
        "    *state = state.wrapping_mul(1_103_515_245).wrapping_add(12_345);\n"
        "    ((*state >> 16) % 201) as i32 - 100\n"
        "}\n\n"
        "fn main() {\n"
        f"    let mut state = {seed & 0xffffffff}u32;\n"
    )
    suffix = "}\n"
    bodies = {
        "simple_sum": (
            f"use {package}::simple_sum;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let a = next_case(&mut state);\n"
            "        let b = next_case(&mut state);\n"
            "        println!(\"{}\", simple_sum(a, b));\n"
            "    }\n"
            f"{suffix}"
        ),
        "boolean_int": (
            f"use {package}::is_even;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        println!(\"{}\", if is_even(value) { 1 } else { 0 });\n"
            "    }\n"
            f"{suffix}"
        ),
        "pointer_length_array": (
            f"use {package}::sum_array;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut values = [0; 8];\n"
            "        let len = ((next_case(&mut state) + 100) % 8 + 1) as usize;\n"
            "        for value in values.iter_mut().take(len) { *value = next_case(&mut state); }\n"
            "        println!(\"{}\", sum_array(&values[..len]));\n"
            "    }\n"
            f"{suffix}"
        ),
        "mutable_buffer": (
            f"use {package}::increment_all;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut values = [0; 8];\n"
            "        let len = ((next_case(&mut state) + 100) % 8 + 1) as usize;\n"
            "        for value in values.iter_mut().take(len) { *value = next_case(&mut state); }\n"
            "        increment_all(&mut values[..len]);\n"
            "        for (index, value) in values[..len].iter().enumerate() {\n"
            "            print!(\"{}{}\", value, if index + 1 == len { \"\\n\" } else { \" \" });\n"
            "        }\n"
            "    }\n"
            f"{suffix}"
        ),
        "multiple_outputs": (
            f"use {package}::divmod_pair;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        let divisor = (next_case(&mut state) + 100) % 19 + 1;\n"
            "        let (quotient, remainder) = divmod_pair(value, divisor);\n"
            "        println!(\"{} {}\", quotient, remainder);\n"
            "    }\n"
            f"{suffix}"
        ),
        "simple_pointer": (
            f"use {package}::increment;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut value = next_case(&mut state);\n"
            "        increment(&mut value);\n"
            "        println!(\"{}\", value);\n"
            "    }\n"
            f"{suffix}"
        ),
        "string_length": (
            f"use {package}::string_length;\n\n"
            f"{prefix}"
            "    let values = [\"\", \"a\", \"hello\", \"migration\", \"safe rust\", \"abcdefghi\"];\n"
            f"    for _ in 0..{case_count} {{\n"
            "        let text = values[((next_case(&mut state) + 100) % 6) as usize];\n"
            "        println!(\"{}\", string_length(text));\n"
            "    }\n"
            f"{suffix}"
        ),
        "output_parameter": (
            f"use {package}::get_max;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut values = [0; 8];\n"
            "        let len = ((next_case(&mut state) + 100) % 9) as usize;\n"
            "        for value in values.iter_mut().take(len) { *value = next_case(&mut state); }\n"
            "        match get_max(&values[..len]) {\n"
            "        Ok(value) => println!(\"0 {}\", value),\n"
            "        Err(status) => println!(\"{} 0\", status),\n"
            "    }\n"
            "    }\n"
            f"{suffix}"
        ),
        "nullable_pointer": (
            f"use {package}::read_value;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        let use_none = (next_case(&mut state) + 100) % 2 == 1;\n"
            "        let result = if use_none { read_value(None) } else { read_value(Some(&value)) };\n"
            "        println!(\"{}\", result.unwrap_or_else(|status| status));\n"
            "    }\n"
            f"{suffix}"
        ),
        "error_code": (
            f"use {package}::divide;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let a = next_case(&mut state);\n"
            "        let b = next_case(&mut state) % 11;\n"
            "        match divide(a, b) {\n"
            "        Ok(value) => println!(\"0 {}\", value),\n"
            "        Err(status) => println!(\"{} 0\", status),\n"
            "    }\n"
            "    }\n"
            f"{suffix}"
        ),
        "malloc_free": (
            f"use {package}::make_value;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let input = next_case(&mut state);\n"
            "        let value = make_value(input);\n"
            "        println!(\"{}\", *value);\n"
            "    }\n"
            f"{suffix}"
        ),
    }
    return bodies.get(project)

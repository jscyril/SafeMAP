from __future__ import annotations

import random
import re
import tempfile
from pathlib import Path

from ..models import CommandResult, ValidationCheck
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
            ["clang", str(c_source), "-o", str(c_binary), "-lm"],
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
        reference_output = c_source.with_suffix(".reference_output")
        reference = (
            _load_llvm_reference_output(reference_output)
            if reference_output.is_file()
            else None
        )
        if reference is not None:
            original = _run_exact([str(c_binary)], c_source.parent)
            mismatch = _reference_mismatch(reference, original)
            if mismatch is not None:
                return ValidationCheck(
                    status="failed",
                    command=original,
                    passed=0,
                    failed=1,
                    reason=(
                        "Original C executable did not match its LLVM reference "
                        f"output: {mismatch}"
                    ),
                )
        package = _package_name(rust_root / "Cargo.toml")
        rust_binary = rust_root / "target" / "debug" / package
        if not rust_binary.exists():
            if reference is not None:
                reference_harness = _build_reference_output_harness(
                    c_source, rust_root, package
                )
                if reference_harness is not None:
                    translated = _run_exact(
                        [str(reference_harness)], rust_root, timeout=120
                    )
                    mismatch = _reference_mismatch(reference, translated)
                    return ValidationCheck(
                        status="passed" if mismatch is None else "failed",
                        command=translated,
                        passed=1 if mismatch is None else 0,
                        failed=0 if mismatch is None else 1,
                        reason=(
                            f"Matched LLVM reference output "
                            f"{reference_output.name}"
                            if mismatch is None
                            else (
                                "Translated Rust reference harness did not match "
                                f"{reference_output.name}: {mismatch}"
                            )
                        ),
                    )
            harness = _build_library_harness(
                c_source, rust_root, package, temporary_path,
                random_inputs=random_inputs, seed=seed,
            )
            if harness is None:
                return ValidationCheck(
                    status="failed" if reference is not None else "not_applicable",
                    passed=0 if reference is not None else None,
                    failed=1 if reference is not None else None,
                    reason=(
                        "LLVM reference output is available, but the translated "
                        "library has no reviewed reference-output harness"
                        if reference is not None
                        else (
                            "Translated project does not produce a comparable "
                            "executable"
                        )
                    ),
                )
            return compare_executables(
                harness.c_command, harness.rust_command, rust_root,
                inputs=inputs, seed=seed,
            )
        if reference is not None:
            translated = _run_exact([str(rust_binary)], rust_root, timeout=120)
            mismatch = _reference_mismatch(reference, translated)
            return ValidationCheck(
                status="passed" if mismatch is None else "failed",
                command=translated,
                passed=1 if mismatch is None else 0,
                failed=0 if mismatch is None else 1,
                reason=(
                    f"Matched LLVM reference output {reference_output.name}"
                    if mismatch is None
                    else (
                        "Translated Rust executable did not match "
                        f"{reference_output.name}: {mismatch}"
                    )
                ),
            )
        return compare_executables(
            [str(c_binary)], [str(rust_binary)], rust_root, inputs=inputs,
            random_inputs=random_inputs, seed=seed,
        )


class _ReferenceOutput:
    def __init__(self, stdout: str, exit_code: int) -> None:
        self.stdout = stdout
        self.exit_code = exit_code


def _load_llvm_reference_output(path: Path) -> _ReferenceOutput:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = re.search(r"(?m)^exit\s+(-?\d+)\s*$", text)
    if match is None:
        raise ValueError(f"LLVM reference output has no exit status: {path}")
    stdout = text[:match.start()]
    return _ReferenceOutput(stdout=stdout, exit_code=int(match.group(1)))


def _run_exact(
    command: list[str],
    cwd: Path,
    stdin: str = "",
    timeout: float = 30,
) -> CommandResult:
    import subprocess

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            command=command,
            cwd=str(cwd),
            exit_code=result.returncode,
            stdout=result.stdout.replace("\r\n", "\n"),
            stderr=result.stderr.replace("\r\n", "\n"),
            status="passed" if result.returncode == 0 else "failed",
        )
    except (subprocess.TimeoutExpired, OSError) as error:
        return CommandResult(
            command=command,
            cwd=str(cwd),
            exit_code=None,
            status="failed",
            reason=str(error),
        )


def _reference_mismatch(
    reference: _ReferenceOutput,
    actual: CommandResult,
) -> str | None:
    if actual.exit_code != reference.exit_code:
        return f"exit code {actual.exit_code!r} != {reference.exit_code}"
    if actual.stdout != reference.stdout:
        expected_lines = reference.stdout.splitlines()
        actual_lines = actual.stdout.splitlines()
        first = next(
            (
                index
                for index, (expected, observed) in enumerate(
                    zip(expected_lines, actual_lines), start=1
                )
                if expected != observed
            ),
            min(len(expected_lines), len(actual_lines)) + 1,
        )
        return (
            f"stdout differs at line {first}; "
            f"expected {len(reference.stdout)} bytes, got {len(actual.stdout)}"
        )
    return None


def _build_reference_output_harness(
    c_source: Path,
    rust_root: Path,
    package: str,
) -> Path | None:
    harness_source = _find_reference_output_harness(c_source)
    if harness_source is None:
        return None
    harness_root = rust_root / "target" / "safemap-reference-output-harness"
    source_dir = harness_root / "src"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "main.rs").write_text(
        harness_source.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (harness_root / "Cargo.toml").write_text(
        "[package]\n"
        'name = "safemap_reference_output_harness"\n'
        'version = "0.1.0"\n'
        'edition = "2021"\n\n'
        "[dependencies]\n"
        f'safemap_generated = {{ package = "{package}", '
        f'path = "{rust_root.as_posix()}" }}\n',
        encoding="utf-8",
    )
    build = run_command(["cargo", "build", "--quiet"], harness_root, timeout=600)
    if build.status != "passed":
        return None
    binary = (
        harness_root
        / "target"
        / "debug"
        / "safemap_reference_output_harness"
    )
    return binary if binary.is_file() else None


def _find_reference_output_harness(c_source: Path) -> Path | None:
    local = c_source.with_suffix(".safemap_harness.rs")
    if local.is_file():
        return local
    project = c_source.parent.name
    for ancestor in c_source.parents:
        candidate = ancestor / "validation_harnesses" / f"{project}.rs"
        if candidate.is_file():
            return candidate
    return None


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
        "simple_subtract": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int a = next_case(&state);\n"
            "        int b = next_case(&state);\n"
            "        printf(\"%d\\n\", subtract(a, b));\n"
            "    }\n"
        ),
        "simple_multiply": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int a = next_case(&state);\n"
            "        int b = next_case(&state);\n"
            "        printf(\"%d\\n\", multiply(a, b));\n"
            "    }\n"
        ),
        "simple_divide": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int a = next_case(&state);\n"
            "        int b = ((next_case(&state) + 100) % 19) + 1;\n"
            "        printf(\"%d\\n\", divide_floor(a, b));\n"
            "    }\n"
        ),
        "simple_modulo": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int a = next_case(&state);\n"
            "        int b = ((next_case(&state) + 100) % 19) + 1;\n"
            "        printf(\"%d\\n\", remainder_value(a, b));\n"
            "    }\n"
        ),
        "boolean_int": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        printf(\"%d\\n\", is_even(value));\n"
            "    }\n"
        ),
        "boolean_negative": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        printf(\"%d\\n\", is_negative(value));\n"
            "    }\n"
        ),
        "boolean_nonzero": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        printf(\"%d\\n\", is_nonzero(value));\n"
            "    }\n"
        ),
        "boolean_greater_equal": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int threshold = next_case(&state);\n"
            "        printf(\"%d\\n\", is_at_least(value, threshold));\n"
            "    }\n"
        ),
        "boolean_less_equal": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int threshold = next_case(&state);\n"
            "        printf(\"%d\\n\", is_at_most(value, threshold));\n"
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
        "array_max": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int arr[8];\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        for (int j = 0; j < len; j++) arr[j] = next_case(&state);\n"
            "        printf(\"%d\\n\", array_max(arr, len));\n"
            "    }\n"
        ),
        "array_total": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int arr[8];\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        for (int j = 0; j < len; j++) arr[j] = next_case(&state);\n"
            "        printf(\"%d\\n\", total_array(arr, len));\n"
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
        "mutable_buffer_decrement": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int arr[8];\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        for (int j = 0; j < len; j++) arr[j] = next_case(&state);\n"
            "        decrement_all(arr, len);\n"
            "        for (int j = 0; j < len; j++) printf(j + 1 == len ? \"%d\\n\" : \"%d \", arr[j]);\n"
            "    }\n"
        ),
        "mutable_buffer_add_two": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int arr[8];\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        for (int j = 0; j < len; j++) arr[j] = next_case(&state);\n"
            "        add_two_all(arr, len);\n"
            "        for (int j = 0; j < len; j++) printf(j + 1 == len ? \"%d\\n\" : \"%d \", arr[j]);\n"
            "    }\n"
        ),
        "mutable_buffer_subtract_two": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int arr[8];\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        for (int j = 0; j < len; j++) arr[j] = next_case(&state);\n"
            "        subtract_two_all(arr, len);\n"
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
        "min_max_outputs": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int a = next_case(&state);\n"
            "        int b = next_case(&state);\n"
            "        int min_value = 0;\n"
            "        int max_value = 0;\n"
            "        min_max_pair(a, b, &min_value, &max_value);\n"
            "        printf(\"%d %d\\n\", min_value, max_value);\n"
            "    }\n"
        ),
        "sum_diff_outputs": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int a = next_case(&state);\n"
            "        int b = next_case(&state);\n"
            "        int sum = 0;\n"
            "        int diff = 0;\n"
            "        sum_diff_pair(a, b, &sum, &diff);\n"
            "        printf(\"%d %d\\n\", sum, diff);\n"
            "    }\n"
        ),
        "output_square": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int out = 0;\n"
            "        square_value(value, &out);\n"
            "        printf(\"%d\\n\", out);\n"
            "    }\n"
        ),
        "output_double": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int out = 0;\n"
            "        double_value(value, &out);\n"
            "        printf(\"%d\\n\", out);\n"
            "    }\n"
        ),
        "simple_pointer": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        increment(&value);\n"
            "        printf(\"%d\\n\", value);\n"
            "    }\n"
        ),
        "simple_pointer_decrement": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        decrement(&value);\n"
            "        printf(\"%d\\n\", value);\n"
            "    }\n"
        ),
        "simple_pointer_double": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        double_in_place(&value);\n"
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
        "string_length_size_t": (
            "    const char *values[] = {\"\", \"a\", \"hello\", \"migration\", \"safe rust\", \"abcdefghi\"};\n"
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        const char *text = values[(next_case(&state) + 100) % 6];\n"
            "        printf(\"%zu\\n\", byte_len(text));\n"
            "    }\n"
        ),
        "string_length_long": (
            "    const char *values[] = {\"\", \"a\", \"hello\", \"migration\", \"safe rust\", \"abcdefghi\"};\n"
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        const char *text = values[(next_case(&state) + 100) % 6];\n"
            "        printf(\"%ld\\n\", string_length_long(text));\n"
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
        "nullable_pointer_zero": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int use_null = (next_case(&state) + 100) % 2;\n"
            "        printf(\"%d\\n\", read_or_zero(use_null ? NULL : &value));\n"
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
        "error_code_product": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int a = next_case(&state);\n"
            "        int b = next_case(&state) % 11;\n"
            "        int out = 0;\n"
            "        int status = multiply_checked(a, b, &out);\n"
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
        "malloc_free_constant": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int *out = make_answer();\n"
            "        printf(\"%d\\n\", *out);\n"
            "        free(out);\n"
            "    }\n"
        ),
        "malloc_vec": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        int *values = make_sequence(len);\n"
            "        for (int j = 0; j < len; j++) printf(j + 1 == len ? \"%d\\n\" : \"%d \", values[j]);\n"
            "        free(values);\n"
            "    }\n"
        ),
        "buffer_metrics": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int arr[8];\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        for (int j = 0; j < len; j++) arr[j] = next_case(&state);\n"
            "        printf(\"%d %d \", sum_values(arr, len), max_value(arr, len));\n"
            "        add_offset(arr, len);\n"
            "        for (int j = 0; j < len; j++) printf(j + 1 == len ? \"%d\\n\" : \"%d \", arr[j]);\n"
            "    }\n"
        ),
        "config_options": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int use_null = (next_case(&state) + 100) % 2;\n"
            "        int flag = next_case(&state);\n"
            "        printf(\"%d %d %d\\n\", read_required(use_null ? NULL : &value), read_or_zero(use_null ? NULL : &value), is_enabled(flag));\n"
            "    }\n"
        ),
        "string_records": (
            "    const char *values[] = {\"\", \"a\", \"hello\", \"migration\", \"safe rust\", \"abcdefghi\"};\n"
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        const char *text = values[(next_case(&state) + 100) % 6];\n"
            "        printf(\"%d %zu %ld\\n\", short_name_len(text), title_len(text), label_len(text));\n"
            "    }\n"
        ),
        "scalar_outputs": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int divisor = next_case(&state) % 11;\n"
            "        int square = 0;\n"
            "        int doubled = 0;\n"
            "        int divided = 0;\n"
            "        int mutable_value = value;\n"
            "        square_and_double(value, &square, &doubled);\n"
            "        int status = divide_checked(value, divisor, &divided);\n"
            "        decrement_in_place(&mutable_value);\n"
            "        printf(\"%d %d %d %d %d\\n\", square, doubled, status, divided, mutable_value);\n"
            "    }\n"
        ),
        "allocation_factory": (
            f"    for (int i = 0; i < {cases}; i++) {{\n"
            "        int value = next_case(&state);\n"
            "        int len = ((next_case(&state) + 100) % 8) + 1;\n"
            "        int *owned = make_owned(value);\n"
            "        int *constant = make_constant();\n"
            "        int *values = make_sequence(len);\n"
            "        printf(\"%d %d \", *owned, *constant);\n"
            "        for (int j = 0; j < len; j++) printf(j + 1 == len ? \"%d\\n\" : \"%d \", values[j]);\n"
            "        free(owned);\n"
            "        free(constant);\n"
            "        free(values);\n"
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
        "simple_subtract": (
            f"use {package}::subtract;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let a = next_case(&mut state);\n"
            "        let b = next_case(&mut state);\n"
            "        println!(\"{}\", subtract(a, b));\n"
            "    }\n"
            f"{suffix}"
        ),
        "simple_multiply": (
            f"use {package}::multiply;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let a = next_case(&mut state);\n"
            "        let b = next_case(&mut state);\n"
            "        println!(\"{}\", multiply(a, b));\n"
            "    }\n"
            f"{suffix}"
        ),
        "simple_divide": (
            f"use {package}::divide_floor;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let a = next_case(&mut state);\n"
            "        let b = (next_case(&mut state) + 100) % 19 + 1;\n"
            "        println!(\"{}\", divide_floor(a, b));\n"
            "    }\n"
            f"{suffix}"
        ),
        "simple_modulo": (
            f"use {package}::remainder_value;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let a = next_case(&mut state);\n"
            "        let b = (next_case(&mut state) + 100) % 19 + 1;\n"
            "        println!(\"{}\", remainder_value(a, b));\n"
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
        "boolean_negative": (
            f"use {package}::is_negative;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        println!(\"{}\", if is_negative(value) { 1 } else { 0 });\n"
            "    }\n"
            f"{suffix}"
        ),
        "boolean_nonzero": (
            f"use {package}::is_nonzero;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        println!(\"{}\", if is_nonzero(value) { 1 } else { 0 });\n"
            "    }\n"
            f"{suffix}"
        ),
        "boolean_greater_equal": (
            f"use {package}::is_at_least;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        let threshold = next_case(&mut state);\n"
            "        println!(\"{}\", if is_at_least(value, threshold) { 1 } else { 0 });\n"
            "    }\n"
            f"{suffix}"
        ),
        "boolean_less_equal": (
            f"use {package}::is_at_most;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        let threshold = next_case(&mut state);\n"
            "        println!(\"{}\", if is_at_most(value, threshold) { 1 } else { 0 });\n"
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
        "array_max": (
            f"use {package}::array_max;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut values = [0; 8];\n"
            "        let len = ((next_case(&mut state) + 100) % 8 + 1) as usize;\n"
            "        for value in values.iter_mut().take(len) { *value = next_case(&mut state); }\n"
            "        println!(\"{}\", array_max(&values[..len]));\n"
            "    }\n"
            f"{suffix}"
        ),
        "array_total": (
            f"use {package}::total_array;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut values = [0; 8];\n"
            "        let len = ((next_case(&mut state) + 100) % 8 + 1) as usize;\n"
            "        for value in values.iter_mut().take(len) { *value = next_case(&mut state); }\n"
            "        println!(\"{}\", total_array(&values[..len]));\n"
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
        "mutable_buffer_decrement": (
            f"use {package}::decrement_all;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut values = [0; 8];\n"
            "        let len = ((next_case(&mut state) + 100) % 8 + 1) as usize;\n"
            "        for value in values.iter_mut().take(len) { *value = next_case(&mut state); }\n"
            "        decrement_all(&mut values[..len]);\n"
            "        for (index, value) in values[..len].iter().enumerate() {\n"
            "            print!(\"{}{}\", value, if index + 1 == len { \"\\n\" } else { \" \" });\n"
            "        }\n"
            "    }\n"
            f"{suffix}"
        ),
        "mutable_buffer_add_two": (
            f"use {package}::add_two_all;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut values = [0; 8];\n"
            "        let len = ((next_case(&mut state) + 100) % 8 + 1) as usize;\n"
            "        for value in values.iter_mut().take(len) { *value = next_case(&mut state); }\n"
            "        add_two_all(&mut values[..len]);\n"
            "        for (index, value) in values[..len].iter().enumerate() {\n"
            "            print!(\"{}{}\", value, if index + 1 == len { \"\\n\" } else { \" \" });\n"
            "        }\n"
            "    }\n"
            f"{suffix}"
        ),
        "mutable_buffer_subtract_two": (
            f"use {package}::subtract_two_all;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut values = [0; 8];\n"
            "        let len = ((next_case(&mut state) + 100) % 8 + 1) as usize;\n"
            "        for value in values.iter_mut().take(len) { *value = next_case(&mut state); }\n"
            "        subtract_two_all(&mut values[..len]);\n"
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
        "min_max_outputs": (
            f"use {package}::min_max_pair;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let a = next_case(&mut state);\n"
            "        let b = next_case(&mut state);\n"
            "        let (min_value, max_value) = min_max_pair(a, b);\n"
            "        println!(\"{} {}\", min_value, max_value);\n"
            "    }\n"
            f"{suffix}"
        ),
        "sum_diff_outputs": (
            f"use {package}::sum_diff_pair;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let a = next_case(&mut state);\n"
            "        let b = next_case(&mut state);\n"
            "        let (sum, diff) = sum_diff_pair(a, b);\n"
            "        println!(\"{} {}\", sum, diff);\n"
            "    }\n"
            f"{suffix}"
        ),
        "output_square": (
            f"use {package}::square_value;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        println!(\"{}\", square_value(value));\n"
            "    }\n"
            f"{suffix}"
        ),
        "output_double": (
            f"use {package}::double_value;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        println!(\"{}\", double_value(value));\n"
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
        "simple_pointer_decrement": (
            f"use {package}::decrement;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut value = next_case(&mut state);\n"
            "        decrement(&mut value);\n"
            "        println!(\"{}\", value);\n"
            "    }\n"
            f"{suffix}"
        ),
        "simple_pointer_double": (
            f"use {package}::double_in_place;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut value = next_case(&mut state);\n"
            "        double_in_place(&mut value);\n"
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
        "string_length_size_t": (
            f"use {package}::byte_len;\n\n"
            f"{prefix}"
            "    let values = [\"\", \"a\", \"hello\", \"migration\", \"safe rust\", \"abcdefghi\"];\n"
            f"    for _ in 0..{case_count} {{\n"
            "        let text = values[((next_case(&mut state) + 100) % 6) as usize];\n"
            "        println!(\"{}\", byte_len(text));\n"
            "    }\n"
            f"{suffix}"
        ),
        "string_length_long": (
            f"use {package}::string_length_long;\n\n"
            f"{prefix}"
            "    let values = [\"\", \"a\", \"hello\", \"migration\", \"safe rust\", \"abcdefghi\"];\n"
            f"    for _ in 0..{case_count} {{\n"
            "        let text = values[((next_case(&mut state) + 100) % 6) as usize];\n"
            "        println!(\"{}\", string_length_long(text));\n"
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
        "nullable_pointer_zero": (
            f"use {package}::read_or_zero;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        let use_none = (next_case(&mut state) + 100) % 2 == 1;\n"
            "        let result = if use_none { read_or_zero(None) } else { read_or_zero(Some(&value)) };\n"
            "        println!(\"{}\", result);\n"
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
        "error_code_product": (
            f"use {package}::multiply_checked;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let a = next_case(&mut state);\n"
            "        let b = next_case(&mut state) % 11;\n"
            "        match multiply_checked(a, b) {\n"
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
        "malloc_free_constant": (
            f"use {package}::make_answer;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = make_answer();\n"
            "        println!(\"{}\", *value);\n"
            "    }\n"
            f"{suffix}"
        ),
        "malloc_vec": (
            f"use {package}::make_sequence;\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let len = (next_case(&mut state) + 100) % 8 + 1;\n"
            "        let values = make_sequence(len);\n"
            "        for (index, value) in values.iter().enumerate() {\n"
            "            print!(\"{}{}\", value, if index + 1 == values.len() { \"\\n\" } else { \" \" });\n"
            "        }\n"
            "    }\n"
            f"{suffix}"
        ),
        "buffer_metrics": (
            f"use {package}::{{add_offset, max_value, sum_values}};\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let mut values = [0; 8];\n"
            "        let len = ((next_case(&mut state) + 100) % 8 + 1) as usize;\n"
            "        for value in values.iter_mut().take(len) { *value = next_case(&mut state); }\n"
            "        print!(\"{} {} \", sum_values(&values[..len]), max_value(&values[..len]));\n"
            "        add_offset(&mut values[..len]);\n"
            "        for (index, value) in values[..len].iter().enumerate() {\n"
            "            print!(\"{}{}\", value, if index + 1 == len { \"\\n\" } else { \" \" });\n"
            "        }\n"
            "    }\n"
            f"{suffix}"
        ),
        "config_options": (
            f"use {package}::{{is_enabled, read_or_zero, read_required}};\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        let use_none = (next_case(&mut state) + 100) % 2 == 1;\n"
            "        let flag = next_case(&mut state);\n"
            "        let required = if use_none { read_required(None) } else { read_required(Some(&value)) };\n"
            "        let optional = if use_none { read_or_zero(None) } else { read_or_zero(Some(&value)) };\n"
            "        println!(\"{} {} {}\", required.unwrap_or_else(|status| status), optional, if is_enabled(flag) { 1 } else { 0 });\n"
            "    }\n"
            f"{suffix}"
        ),
        "string_records": (
            f"use {package}::{{label_len, short_name_len, title_len}};\n\n"
            f"{prefix}"
            "    let values = [\"\", \"a\", \"hello\", \"migration\", \"safe rust\", \"abcdefghi\"];\n"
            f"    for _ in 0..{case_count} {{\n"
            "        let text = values[((next_case(&mut state) + 100) % 6) as usize];\n"
            "        println!(\"{} {} {}\", short_name_len(text), title_len(text), label_len(text));\n"
            "    }\n"
            f"{suffix}"
        ),
        "scalar_outputs": (
            f"use {package}::{{decrement_in_place, divide_checked, square_and_double}};\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        let divisor = next_case(&mut state) % 11;\n"
            "        let (square, doubled) = square_and_double(value);\n"
            "        let mut mutable_value = value;\n"
            "        decrement_in_place(&mut mutable_value);\n"
            "        match divide_checked(value, divisor) {\n"
            "        Ok(divided) => println!(\"{} {} 0 {} {}\", square, doubled, divided, mutable_value),\n"
            "        Err(status) => println!(\"{} {} {} 0 {}\", square, doubled, status, mutable_value),\n"
            "    }\n"
            "    }\n"
            f"{suffix}"
        ),
        "allocation_factory": (
            f"use {package}::{{make_constant, make_owned, make_sequence}};\n\n"
            f"{prefix}"
            f"    for _ in 0..{case_count} {{\n"
            "        let value = next_case(&mut state);\n"
            "        let len = (next_case(&mut state) + 100) % 8 + 1;\n"
            "        let owned = make_owned(value);\n"
            "        let constant = make_constant();\n"
            "        let values = make_sequence(len);\n"
            "        print!(\"{} {} \", *owned, *constant);\n"
            "        for (index, value) in values.iter().enumerate() {\n"
            "            print!(\"{}{}\", value, if index + 1 == values.len() { \"\\n\" } else { \" \" });\n"
            "        }\n"
            "    }\n"
            f"{suffix}"
        ),
    }
    return bodies.get(project)

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from .models import CommandResult


def run_command(
    command: list[str],
    cwd: Path,
    timeout: float = 120.0,
    env: dict[str, str] | None = None,
) -> CommandResult:
    start = time.monotonic()
    executable = command[0]
    if shutil.which(executable) is None:
        return CommandResult(
            command=command,
            cwd=str(cwd),
            exit_code=None,
            duration_seconds=time.monotonic() - start,
            status="unsupported",
            reason=f"Executable not found: {executable}",
        )
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            command=command,
            cwd=str(cwd),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=time.monotonic() - start,
            status="passed" if completed.returncode == 0 else "failed",
        )
    except subprocess.TimeoutExpired as error:
        return CommandResult(
            command=command,
            cwd=str(cwd),
            exit_code=None,
            stdout=_text(error.stdout),
            stderr=_text(error.stderr),
            duration_seconds=time.monotonic() - start,
            status="failed",
            reason=f"Timed out after {timeout} seconds",
        )


def _text(value: str | bytes | None) -> str:
    # TimeoutExpired carries bytes even when text=True was requested.
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""

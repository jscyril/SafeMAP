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
            stdout=error.stdout or "",
            stderr=error.stderr or "",
            duration_seconds=time.monotonic() - start,
            status="failed",
            reason=f"Timed out after {timeout} seconds",
        )


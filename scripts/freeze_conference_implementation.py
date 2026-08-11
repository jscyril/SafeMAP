from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "research" / "conference_evaluation.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "research" / "implementation_freeze.json"
REQUIRED_INPUTS = (
    REPO_ROOT / "research" / "CONFERENCE_EVALUATION_PROTOCOL.md",
    REPO_ROOT / "research" / "development_corpus_manifest.json",
    REPO_ROOT / "research" / "heldout_corpus_manifest.json",
)
PLACEHOLDER_MODEL_MARKERS = (
    "replace",
    "configurable",
    "placeholder",
    "model-name",
    "to_be_frozen",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(
    command: list[str],
    *,
    cwd: Path = REPO_ROOT,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def _git_head() -> str:
    return _run(["git", "rev-parse", "HEAD"]).stdout.strip()


def _assert_clean_worktree() -> None:
    status = _run(["git", "status", "--porcelain"]).stdout.strip()
    if status:
        raise ValueError(
            "Implementation freeze requires a clean committed worktree"
        )


def _assert_no_runtime_config_overrides() -> None:
    overrides = [
        name for name in ("SAFEMAP_MODEL", "SAFEMAP_BASE_URL")
        if os.getenv(name)
    ]
    if overrides:
        raise ValueError(
            "Implementation freeze requires the model and base URL from the "
            "hashed conference configuration; unset runtime override(s): "
            + ", ".join(overrides)
        )


def validate_conference_config(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Conference configuration must be a mapping")
    llm = raw.get("llm")
    validation = raw.get("validation")
    translation = raw.get("translation")
    if not all(
        isinstance(item, dict)
        for item in (llm, validation, translation)
    ):
        raise ValueError(
            "Conference configuration requires translation, llm, and "
            "validation mappings"
        )
    model = str(llm.get("model", "")).strip()
    lowered = model.lower()
    if not model or any(
        marker in lowered for marker in PLACEHOLDER_MODEL_MARKERS
    ):
        raise ValueError(
            "Choose and record the exact competitive-baseline model before "
            "freezing"
        )
    if float(llm.get("temperature", -1)) != 0.0:
        raise ValueError(
            "Conference direct-LLM baseline temperature must be 0.0"
        )
    if int(validation.get("differential_test_inputs", 0)) < 1000:
        raise ValueError(
            "Conference differential validation requires at least 1000 "
            "generated cases"
        )
    if not validation.get("run_c_sanitizers"):
        raise ValueError("Conference configuration must enable C sanitizers")
    required_components = (
        "use_static_guidance",
        "use_pointer_roles",
        "use_safe_signatures",
        "use_dependency_grouping",
        "use_idiom_plans",
        "use_validation_feedback",
        "forbid_unsafe",
    )
    missing = [
        name for name in required_components
        if not translation.get(name)
    ]
    if missing:
        raise ValueError(
            "Full conference configuration disabled required components: "
            + ", ".join(missing)
        )
    return raw


def _tool_version(command: list[str]) -> str:
    result = _run(command, check=False)
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0] if output else "unavailable"


def freeze(
    config: Path,
    output: Path,
    development_artifacts: list[Path],
) -> dict:
    if output.exists():
        raise FileExistsError(
            f"Refusing to replace existing freeze record: {output}"
        )
    validate_conference_config(config)
    _assert_no_runtime_config_overrides()
    _assert_clean_worktree()
    test = _run(["python", "-m", "pytest", "-q"])
    artifacts = [config, *REQUIRED_INPUTS, *development_artifacts]
    missing = [path for path in artifacts if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing freeze input(s): "
            + ", ".join(str(path) for path in missing)
        )
    record = {
        "freeze_schema_version": "safemap.implementation_freeze.v1",
        "status": "frozen",
        "frozen_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "git_commit": _git_head(),
        "git_worktree": "clean",
        "runtime_config_overrides": "none",
        "python": platform.python_version(),
        "test_command": ["python", "-m", "pytest", "-q"],
        "test_status": "passed",
        "test_output": test.stdout.strip(),
        "tools": {
            "clang": _tool_version(["clang", "--version"]),
            "rustc": _tool_version(["rustc", "--version"]),
            "cargo": _tool_version(["cargo", "--version"]),
            "clippy": _tool_version(["cargo", "clippy", "--version"]),
            "miri": _tool_version(["cargo", "miri", "--version"]),
            "c2rust": _tool_version(["c2rust", "--version"]),
        },
        "frozen_inputs": [
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": _sha256(path),
            }
            for path in artifacts
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze a clean, tested SafeMAP implementation and bind it to "
            "the conference configuration and development artifacts."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    parser.add_argument(
        "--development-artifact",
        action="append",
        type=Path,
        default=[],
    )
    args = parser.parse_args()
    record = freeze(
        args.config.resolve(),
        args.output.resolve(),
        [path.resolve() for path in args.development_artifact],
    )
    print(
        f"froze {record['git_commit']} in {args.output.resolve()}"
    )


if __name__ == "__main__":
    main()

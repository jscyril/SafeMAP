from __future__ import annotations

import json
import os
import platform
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import JsonModel

ARTIFACT_DIRS = (
    "analysis", "baseline", "plans", "rewrites", "prompts", "responses",
    "repair", "validation", "logs", "reports", "final",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        for name in ARTIFACT_DIRS:
            (self.root / name).mkdir(parents=True, exist_ok=True)

    @classmethod
    def create(cls, base: Path, project_name: str) -> "ArtifactStore":
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = uuid.uuid4().hex[:8]
        return cls(base / ".safemap" / "runs" / f"{stamp}-{project_name}-{run_id}")

    def path(self, relative: str) -> Path:
        return self.root / relative

    def write_json(self, relative: str, value: JsonModel | dict[str, Any] | list[Any]) -> Path:
        data = value.to_dict() if isinstance(value, JsonModel) else value
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(target, json.dumps(data, indent=2, sort_keys=True) + "\n")
        return target

    def read_json(self, relative: str) -> Any:
        return json.loads(self.path(relative).read_text(encoding="utf-8"))

    def write_text(self, relative: str, value: str) -> Path:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(target, value)
        return target

    def record_environment(self) -> None:
        self.write_json("environment.json", {
            "created_at": utc_now(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pid": os.getpid(),
        })


def _atomic_write(target: Path, contents: str) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, delete=False
    ) as handle:
        handle.write(contents)
        temporary = Path(handle.name)
    temporary.replace(target)


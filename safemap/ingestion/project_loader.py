from __future__ import annotations

import re
from pathlib import Path

from ..artifacts import ArtifactStore, utc_now
from ..models import ProjectInfo
from .compile_db import prepare_compile_database
from .file_discovery import detect_build_system, discover_files


def ingest_project(input_path: str | Path, store: ArtifactStore) -> ProjectInfo:
    source = Path(input_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input does not exist: {source}")
    if source.is_file() and source.suffix.lower() != ".c":
        raise ValueError("Single-file input must be a .c file")
    root = source.parent if source.is_file() else source
    discovered = discover_files(source)
    if not discovered["c_files"]:
        raise ValueError(f"No C source files found under {source}")
    build_system = detect_build_system(
        source, discovered["build_files"], discovered["c_files"]
    )
    database, generation = prepare_compile_database(
        root, build_system, discovered["c_files"], store.path("compile_db")
    )
    if generation:
        store.write_json("logs/compile_db.json", generation)
    entrypoints = []
    for c_file in discovered["c_files"]:
        if re.search(r"\bmain\s*\(", c_file.read_text(encoding="utf-8", errors="replace")):
            entrypoints.append(str(c_file))
    test_commands: list[list[str]] = []
    if any(item.name in {"Makefile", "makefile"} for item in discovered["build_files"]):
        test_commands.append(["make", "test"])
    project = ProjectInfo(
        project_name=source.stem if source.is_file() else source.name,
        root=str(root),
        input_path=str(source),
        c_files=[str(item) for item in discovered["c_files"]],
        header_files=[str(item) for item in discovered["header_files"]],
        build_files=[str(item) for item in discovered["build_files"]],
        test_files=[str(item) for item in discovered["test_files"]],
        build_system=build_system,
        compile_commands=str(database) if database else None,
        test_commands=test_commands,
        detected_entrypoints=entrypoints,
        created_at=utc_now(),
    )
    store.write_json("project.json", project)
    return project

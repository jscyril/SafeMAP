from pathlib import Path

import pytest

from scripts.reproduce_paper_artifacts import (
    PUBLICATION_ARTIFACTS,
    publish_snapshot,
)


def test_publish_snapshot_copies_only_canonical_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "work"
    destination = tmp_path / "publication"
    for name in PUBLICATION_ARTIFACTS:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"artifact: {name}\n", encoding="utf-8")
    harness = source / "final/.safemap/runs/old/final/rust/target/debug/output"
    harness.parent.mkdir(parents=True)
    harness.write_text("must not be published", encoding="utf-8")

    published = publish_snapshot(source, destination)

    assert len(published) == len(PUBLICATION_ARTIFACTS)
    assert all(len(item["sha256"]) == 64 for item in published)
    for name in PUBLICATION_ARTIFACTS:
        assert (destination / name).read_text(encoding="utf-8") == (
            f"artifact: {name}\n"
        )
    assert not (destination / "final/.safemap").exists()


def test_publish_snapshot_rejects_incomplete_artifacts_before_copying(
    tmp_path: Path,
) -> None:
    source = tmp_path / "work"
    source.mkdir()
    destination = tmp_path / "publication"

    with pytest.raises(FileNotFoundError, match="incomplete artifact set"):
        publish_snapshot(source, destination)

    assert not destination.exists()


def test_publish_snapshot_rejects_unexpected_existing_files(tmp_path: Path) -> None:
    source = tmp_path / "work"
    destination = tmp_path / "publication"
    for name in PUBLICATION_ARTIFACTS:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("current\n", encoding="utf-8")
    stale = destination / "final/.safemap/runs/old/output"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="unexpected files"):
        publish_snapshot(source, destination)

    assert stale.exists()


def test_publish_snapshot_includes_explicit_extra_artifact(tmp_path: Path) -> None:
    source = tmp_path / "work"
    destination = tmp_path / "publication"
    for name in PUBLICATION_ARTIFACTS:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("current\n", encoding="utf-8")
    llm_result = source / "llm-subset/benchmark_results.csv"
    llm_result.parent.mkdir(parents=True)
    llm_result.write_text("project,mode\ndemo,llm_only\n", encoding="utf-8")

    publish_snapshot(
        source,
        destination,
        extra_artifacts=("llm-subset/benchmark_results.csv",),
    )

    assert (destination / "llm-subset/benchmark_results.csv").read_text(
        encoding="utf-8"
    ) == "project,mode\ndemo,llm_only\n"

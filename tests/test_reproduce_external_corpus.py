from pathlib import Path

import pytest

from scripts.reproduce_external_corpus import (
    EXTERNAL_ARTIFACTS,
    publish_external_snapshot,
)


def _complete_source(root: Path) -> None:
    root.mkdir()
    for name in EXTERNAL_ARTIFACTS:
        (root / name).write_text(name + "\n", encoding="utf-8")


def test_external_snapshot_requires_complete_artifact_set(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()

    with pytest.raises(FileNotFoundError, match="incomplete external artifact"):
        publish_external_snapshot(source, tmp_path / "snapshot")


def test_external_snapshot_rejects_unexpected_destination_files(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    _complete_source(source)
    destination = tmp_path / "snapshot"
    destination.mkdir()
    (destination / "stale.txt").write_text("stale\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="unexpected files"):
        publish_external_snapshot(source, destination)


def test_external_snapshot_publishes_only_allowlisted_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _complete_source(source)
    destination = tmp_path / "snapshot"

    published = publish_external_snapshot(source, destination)

    assert {Path(item["path"]).name for item in published} == set(EXTERNAL_ARTIFACTS)
    assert {path.name for path in destination.iterdir()} == set(EXTERNAL_ARTIFACTS)

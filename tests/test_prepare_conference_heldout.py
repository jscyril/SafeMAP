from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.prepare_conference_heldout import prepare


def test_heldout_preparation_refuses_to_run_without_freeze(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"projects": []}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="sealed"):
        prepare(
            tmp_path / "sources",
            tmp_path / "output",
            manifest_path=manifest,
            freeze_path=tmp_path / "missing-freeze.json",
        )


def test_heldout_preparation_rejects_non_frozen_record(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"projects": []}), encoding="utf-8")
    freeze = tmp_path / "freeze.json"
    freeze.write_text(
        json.dumps({"status": "development", "git_commit": "unused"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="status"):
        prepare(
            tmp_path / "sources",
            tmp_path / "output",
            manifest_path=manifest,
            freeze_path=freeze,
        )

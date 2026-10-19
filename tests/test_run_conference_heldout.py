from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.run_conference_heldout import merge_stage_results


def _write_results(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["project", "mode", "status"])
        writer.writeheader()
        writer.writerows(rows)


def test_merge_stage_results_is_sorted_and_complete(tmp_path: Path) -> None:
    first = tmp_path / "non-llm"
    second = tmp_path / "llm"
    _write_results(first / "benchmark_results.csv", [
        {"project": "libcsv", "mode": "safemap_deterministic", "status": "completed"},
        {"project": "cjson", "mode": "c2rust_only", "status": "completed"},
    ])
    _write_results(second / "benchmark_results.csv", [
        {"project": "cjson", "mode": "llm_only", "status": "failed"},
    ])

    output = tmp_path / "combined.csv"
    assert merge_stage_results([first, second], output) == 3
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [(row["project"], row["mode"]) for row in rows] == [
        ("cjson", "c2rust_only"),
        ("cjson", "llm_only"),
        ("libcsv", "safemap_deterministic"),
    ]


def test_merge_stage_results_rejects_duplicate_project_mode(tmp_path: Path) -> None:
    first = tmp_path / "non-llm"
    second = tmp_path / "llm"
    row = {"project": "inih", "mode": "llm_only", "status": "completed"}
    _write_results(first / "benchmark_results.csv", [row])
    _write_results(second / "benchmark_results.csv", [row])

    with pytest.raises(ValueError, match="duplicate"):
        merge_stage_results([first, second], tmp_path / "combined.csv")


def test_merge_stage_results_rejects_schema_drift(tmp_path: Path) -> None:
    first = tmp_path / "non-llm"
    second = tmp_path / "llm"
    _write_results(first / "benchmark_results.csv", [
        {"project": "inih", "mode": "c2rust_only", "status": "completed"},
    ])
    second.mkdir(parents=True)
    (second / "benchmark_results.csv").write_text(
        "project,mode,reason\ninih,llm_only,quota\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="schemas differ"):
        merge_stage_results([first, second], tmp_path / "combined.csv")


def test_quota_wait_uses_provider_hint() -> None:
    from scripts.run_conference_heldout import quota_wait_seconds

    assert quota_wait_seconds("Please retry in 9h38m2.5s.") == 3600  # capped
    assert quota_wait_seconds("Please retry in 41s") == 161
    assert quota_wait_seconds("HTTP 503") == 3600


def test_v2_stage_waits_out_quota_and_resumes(tmp_path: Path, monkeypatch) -> None:
    import subprocess
    from types import SimpleNamespace

    from scripts import run_conference_heldout as runner

    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "manifest.json").write_text("{}", encoding="utf-8")
    config = tmp_path / "c.yaml"
    config.write_text("", encoding="utf-8")
    monkeypatch.setattr(runner, "_verify_inputs", lambda *a, **k: {"git_commit": "x"})
    results = iter([
        SimpleNamespace(returncode=1, stderr="ProviderUnavailable: HTTP 429 Please retry in 30s"),
        SimpleNamespace(returncode=0, stderr=""),
    ])
    runs, sleeps = [], []
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: (runs.append(1), next(results))[1])
    monkeypatch.setattr(runner.time, "sleep", sleeps.append)
    work = tmp_path / "work"
    (work / "v2-llm").mkdir(parents=True)  # interrupted earlier
    with pytest.raises(FileExistsError):
        runner.run_stage("v2-llm", work, corpus, config, tmp_path / "f.json")
    plan = runner.run_stage("v2-llm", work, corpus, config, tmp_path / "f.json", resume=True)
    assert len(runs) == 2 and sleeps == [150]
    assert plan["modes"] == ["safemap_guided", "llm_only"]
    assert len(plan["provider_waits"]) == 1
    # A completed stage is never reused, even with --resume.
    with pytest.raises(FileExistsError):
        runner.run_stage("v2-llm", work, corpus, config, tmp_path / "f.json", resume=True)

    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=2, stderr="boom"))
    with pytest.raises(subprocess.CalledProcessError):
        runner.run_stage("v2-non-llm", tmp_path / "w2", corpus, config, tmp_path / "f.json")


def test_only_development_stages_accept_a_corpus_from_another_freeze(tmp_path: Path, monkeypatch) -> None:
    import json

    from scripts import run_conference_heldout as runner

    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "manifest.json").write_text(json.dumps({"freeze_git_commit": "v1"}))
    config = runner.REPO_ROOT / "research" / "resubmission_evaluation.yaml"
    freeze = {"git_commit": "v2", "frozen_inputs": [
        {"path": "research/resubmission_evaluation.yaml", "sha256": runner._sha256(config)}]}
    monkeypatch.setattr(runner, "_load_and_verify_freeze", lambda path: freeze)
    for name in runner.RUNTIME_OVERRIDES:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValueError, match="different freeze"):
        runner._verify_inputs(tmp_path / "f.json", corpus, config)
    assert runner._verify_inputs(tmp_path / "f.json", corpus, config, development=True) is freeze
    assert set(runner.DEVELOPMENT_STAGES) == {"v2-ablation"}

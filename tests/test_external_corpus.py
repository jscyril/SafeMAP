import hashlib
import json
from pathlib import Path

from safemap.analysis.c_analyzer import _analyze_fallback
from safemap.models import ProjectInfo
from scripts.prepare_external_corpus import (
    ARCHITECTURE_GATED_SOURCES,
    EXPECTED_SELECTION,
    MAX_SOURCE_LINES,
)


CORPUS = Path("external_corpus/llvm_test_suite_misc")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_external_corpus_manifest_is_complete_and_outcome_blind() -> None:
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["corpus_schema_version"] == "safemap.external_corpus.v1"
    assert manifest["selection"]["outcome_blind"] is True
    assert (
        manifest["selection"]["maximum_physical_source_lines"]
        == MAX_SOURCE_LINES
    )
    assert set(manifest["selection"]["architecture_gated_sources_excluded"]) == (
        ARCHITECTURE_GATED_SOURCES
    )
    assert {item["source"] for item in manifest["projects"]} == EXPECTED_SELECTION
    assert len(manifest["projects"]) == 10


def test_external_corpus_files_match_manifest_hashes() -> None:
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))

    for item in manifest["projects"]:
        project = CORPUS / "projects" / item["project"]
        source = project / item["source"]
        reference = project / item["reference_output"]
        assert source.is_file()
        assert reference.is_file()
        assert _sha256(source) == item["source_sha256"]
        assert _sha256(reference) == item["reference_output_sha256"]
        assert len(source.read_text(encoding="utf-8").splitlines()) == item["lines"]
        assert item["lines"] <= MAX_SOURCE_LINES


def test_external_corpus_can_be_analyzed_without_expected_labels() -> None:
    for project in sorted((CORPUS / "projects").iterdir()):
        sources = sorted(project.glob("*.c"))
        assert len(sources) == 1
        assert not (project / "expected.json").exists()
        analysis = _analyze_fallback(ProjectInfo(c_files=[str(sources[0])]))
        assert analysis.functions, project.name

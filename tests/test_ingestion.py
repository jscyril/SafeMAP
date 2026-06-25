from pathlib import Path

from safemap.artifacts import ArtifactStore
from safemap.ingestion.project_loader import ingest_project


def test_ingests_single_file_and_creates_compile_database(tmp_path: Path) -> None:
    source = tmp_path / "main.c"
    source.write_text("int main(void) { return 0; }")
    store = ArtifactStore(tmp_path / "work")

    project = ingest_project(source, store)

    assert project.build_system == "single_file"
    assert project.detected_entrypoints == [str(source)]
    assert Path(project.compile_commands).exists()
    assert store.path("project.json").exists()


def test_ingests_single_source_directory_and_creates_compile_database(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    source = project_dir / "main.c"
    source.write_text("int main(void) { return 0; }")
    store = ArtifactStore(tmp_path / "work")

    project = ingest_project(project_dir, store)

    assert project.build_system == "single_file"
    assert Path(project.compile_commands).exists()

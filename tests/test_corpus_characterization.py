from __future__ import annotations

from pathlib import Path

from safemap.evaluation.corpus_characterization import (
    characterize_corpus,
    write_characterization,
)


def test_characterization_exports_required_distributions(
    tmp_path: Path,
) -> None:
    project_a = tmp_path / "projects" / "alpha"
    project_b = tmp_path / "projects" / "beta"
    project_a.mkdir(parents=True)
    project_b.mkdir(parents=True)
    (project_a / "alpha.c").write_text(
        "double dot(const double *x, int n) { "
        "double total=0; for(int i=0;i<n;i++) total += x[i]; "
        "return total; }\n",
        encoding="utf-8",
    )
    (project_b / "beta.c").write_text(
        "unsigned reverse(unsigned x) { return (x >> 1) | (x << 1); }\n"
        "int main(void) { return 0; }\n",
        encoding="utf-8",
    )

    result = characterize_corpus(tmp_path)

    assert result["project_count"] == 2
    assert result["function_count"] == 3
    assert result["source_loc"] == 3
    assert result["function_distributions"]["pointer_density"]["count"] == 3
    assert result["construct_distribution"]["loop"] == 1
    assert result["construct_distribution"]["bit_operation"] == 1
    assert result["construct_distribution"]["entry_point"] == 1


def test_characterization_writes_json_and_function_csv(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    project.mkdir()
    (project / "main.c").write_text(
        "int main(void) { return 0; }\n",
        encoding="utf-8",
    )
    output_json = tmp_path / "out" / "characterization.json"
    output_csv = tmp_path / "out" / "functions.csv"

    write_characterization(tmp_path, output_json, output_csv)

    assert output_json.is_file()
    assert output_csv.is_file()
    assert "pointer_density" in output_csv.read_text(encoding="utf-8")

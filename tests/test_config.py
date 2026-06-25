from pathlib import Path

import pytest

from safemap.config import load_config


def test_loads_nested_yaml(tmp_path: Path) -> None:
    path = tmp_path / "safemap.yaml"
    path.write_text(
        "translation:\n"
        "  max_repair_attempts: 2\n"
        "validation:\n"
        "  run_miri: true\n"
    )
    config = load_config(path)
    assert config.translation.max_repair_attempts == 2
    assert config.validation.run_miri is True


def test_rejects_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("translation:\n  imaginary: true\n")
    with pytest.raises(ValueError, match="Unknown configuration key"):
        load_config(path)


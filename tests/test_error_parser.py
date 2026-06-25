import json

from safemap.repair.error_parser import parse_cargo_diagnostics


def test_parses_cargo_json_diagnostic() -> None:
    output = json.dumps({
        "reason": "compiler-message",
        "message": {
            "code": {"code": "E0308"},
            "level": "error",
            "message": "mismatched types",
            "rendered": "error[E0308]",
            "spans": [{
                "is_primary": True, "file_name": "src/lib.rs",
                "line_start": 3, "column_start": 4,
            }],
        },
    })
    result = parse_cargo_diagnostics(output)
    assert result[0].code == "E0308"
    assert result[0].line == 3


from __future__ import annotations

import json
from pathlib import Path

from scripts.build_reviewer_website import build


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_reviewer_website_uses_frozen_outcome_blind_packet(tmp_path: Path) -> None:
    source_site = REPO_ROOT / "docs-site" / "review"
    site = tmp_path / "review"
    site.mkdir()
    for name in ("index.html", "site.css", "README.md"):
        (site / name).write_bytes((source_site / name).read_bytes())

    result = build(
        REPO_ROOT / "research" / "reviewer_packets" / "frozen_packet_ui2",
        site,
        REPO_ROOT
        / "research"
        / "reviewer_packets"
        / "conference-heldout-eligibility-ui2.zip",
    )

    assert result["outcome_blind"] is True
    assert result["function_count"] == 146
    assert result["packet_sha256"] == (
        "395125387fc42e16c1c07c2bd5d7c0b4c3594acaa396ec7eb8de570724a33540"
    )
    assert "Complete codebook" in (site / "form.html").read_text(encoding="utf-8")
    assert (site / "sources/projects/cjson/cJSON.c").is_file()
    assert (site / "SafeMAP-reviewer-packet-ui2.zip").is_file()
    manifest = json.loads((site / "site_manifest.json").read_text(encoding="utf-8"))
    assert manifest["response_transport"] == "local_export_only"

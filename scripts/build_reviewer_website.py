#!/usr/bin/env python3
"""Build the static, outcome-blind reviewer website from frozen packet UI2."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET = REPO_ROOT / "research" / "reviewer_packets" / "frozen_packet_ui2"
DEFAULT_SITE = REPO_ROOT / "docs-site" / "review"
DEFAULT_ZIP = (
    REPO_ROOT
    / "research"
    / "reviewer_packets"
    / "conference-heldout-eligibility-ui2.zip"
)
EXPECTED_PACKET_SHA256 = (
    "395125387fc42e16c1c07c2bd5d7c0b4c3594acaa396ec7eb8de570724a33540"
)

PAGES = (
    ("REVIEWER_HANDOFF.md", "instructions.html", "Reviewer instructions"),
    ("REVIEWER_CONSENT_AND_SCREENING.md", "consent.html", "Consent and screening"),
    ("REVIEWER_CODEBOOK.md", "codebook.html", "Eligibility codebook"),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inline(value: str) -> str:
    escaped = html.escape(value, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def _markdown_to_html(source: str) -> str:
    """Render the limited Markdown used by the three frozen reviewer documents."""

    output: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    list_items: list[str] = []
    in_quote = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append("<p>" + _inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            output.extend(f"<li>{_inline(item)}</li>" for item in list_items)
            output.append(f"</{list_type}>")
            list_type = None
            list_items.clear()

    def close_quote() -> None:
        nonlocal in_quote
        if in_quote:
            output.append("</blockquote>")
            in_quote = False

    for raw in source.splitlines():
        line = raw.rstrip()
        if not line:
            flush_paragraph()
            close_list()
            close_quote()
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            close_quote()
            level = len(heading.group(1))
            output.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue
        quote = re.match(r"^>\s?(.*)$", line)
        if quote:
            flush_paragraph()
            close_list()
            if not in_quote:
                output.append("<blockquote>")
                in_quote = True
            output.append(f"<p>{_inline(quote.group(1))}</p>")
            continue
        close_quote()
        bullet = re.match(r"^-\s+(.+)$", line)
        numbered = re.match(r"^\d+\.\s+(.+)$", line)
        item = bullet or numbered
        if item:
            flush_paragraph()
            wanted = "ul" if bullet else "ol"
            if list_type != wanted:
                close_list()
                output.append(f"<{wanted}>")
                list_type = wanted
            list_items.append(item.group(1))
            continue
        if list_type:
            list_items[-1] += " " + line.strip()
            continue
        close_list()
        paragraph.append(line.strip())

    flush_paragraph()
    close_list()
    close_quote()
    return "\n".join(output)


def _document(title: str, content: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · SafeMAP Independent Review</title>
  <link rel="stylesheet" href="site.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <header class="site-header">
    <a class="identity" href="index.html"><span class="mark" aria-hidden="true">SM</span>
      <span><strong>SafeMAP</strong><small>Independent eligibility review</small></span></a>
    <span class="status">Outcome-blind packet · UI2</span>
  </header>
  <main id="main" class="document">
    <section>
      <nav><a href="index.html">← Reviewer home</a> · <a href="instructions.html">Instructions</a>
        · <a href="consent.html">Consent</a> · <a href="codebook.html">Codebook</a>
        · <a href="form.html">Review form</a></nav>
      {content}
    </section>
  </main>
  <footer><p>SafeMAP independent review · Static site hosted with GitHub Pages</p></footer>
</body>
</html>
"""


def _verify_packet(packet: Path) -> dict[str, object]:
    manifest = json.loads((packet / "packet_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("packet_sha256") != EXPECTED_PACKET_SHA256:
        raise ValueError("Refusing to publish an unexpected reviewer packet")
    if manifest.get("outcome_blind") is not True or manifest.get("function_count") != 146:
        raise ValueError("Reviewer packet is not the frozen outcome-blind inventory")
    bad: list[str] = []
    for item in manifest["files"]:
        path = packet / str(item["path"])
        if not path.is_file() or _sha256(path) != item["sha256"]:
            bad.append(str(item["path"]))
    if bad:
        raise ValueError("Packet file verification failed: " + ", ".join(bad))
    return manifest


def build(packet: Path, site: Path, zip_path: Path) -> dict[str, object]:
    manifest = _verify_packet(packet)
    required_authored = (site / "index.html", site / "site.css", site / "README.md")
    missing = [path for path in required_authored if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing authored site file(s): " + ", ".join(map(str, missing)))
    if not zip_path.is_file():
        raise FileNotFoundError(zip_path)

    for source_name, output_name, title in PAGES:
        source = (packet / source_name).read_text(encoding="utf-8")
        if source_name == "REVIEWER_HANDOFF.md":
            source = source.replace(
                "Read `REVIEWER_CODEBOOK.md` completely.",
                "Read the complete eligibility codebook from the website navigation.",
            ).replace(
                "Open `review.html` locally in a current browser.",
                "Open the review form from the website navigation in a current browser.",
            )
        elif source_name == "REVIEWER_CONSENT_AND_SCREENING.md":
            source = source.replace(
                "Complete this privately before receiving the function-label packet.",
                "Complete this privately with the coordinator before beginning the function-label review.",
            )
        rendered = _markdown_to_html(source)
        (site / output_name).write_text(_document(title, rendered), encoding="utf-8")
        shutil.copy2(packet / source_name, site / source_name)

    form = (packet / "review.html").read_text(encoding="utf-8")
    form = form.replace(
        "<body>",
        '<body>\n<nav style="padding:8px 18px;background:#eaf4f7;border-bottom:1px solid #c8d2dc">'
        '<a href="index.html">Reviewer home</a> · <a href="instructions.html">Instructions</a> · '
        '<a href="codebook.html">Complete codebook</a></nav>',
        1,
    )
    form = form.replace(
        "Read <code>REVIEWER_CODEBOOK.md</code> before using this reference.",
        'Read the <a href="codebook.html">complete reviewer codebook</a> before using this reference.',
        1,
    )
    (site / "form.html").write_text(form, encoding="utf-8")

    shutil.copytree(packet / "sources", site / "sources", dirs_exist_ok=True)
    shutil.copy2(packet / "packet_manifest.json", site / "packet_manifest.json")
    shutil.copy2(packet / "function_inventory.json", site / "function_inventory.json")
    shutil.copy2(zip_path, site / "SafeMAP-reviewer-packet-ui2.zip")

    generated = sorted(
        path for path in site.rglob("*")
        if path.is_file() and path.name != "site_manifest.json"
    )
    site_manifest = {
        "schema_version": "safemap.reviewer_site.v1",
        "outcome_blind": True,
        "packet_sha256": manifest["packet_sha256"],
        "codebook_sha256": manifest["codebook_sha256"],
        "function_count": manifest["function_count"],
        "response_transport": "local_export_only",
        "files": [
            {
                "path": str(path.relative_to(site)),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in generated
        ],
    }
    (site / "site_manifest.json").write_text(
        json.dumps(site_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return site_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--site", type=Path, default=DEFAULT_SITE)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=DEFAULT_ZIP)
    args = parser.parse_args()
    result = build(args.packet.resolve(), args.site.resolve(), args.zip_path.resolve())
    print(json.dumps({
        "packet_sha256": result["packet_sha256"],
        "function_count": result["function_count"],
        "file_count": len(result["files"]),
    }, indent=2))


if __name__ == "__main__":
    main()

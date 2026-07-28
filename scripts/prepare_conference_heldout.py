from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "research" / "heldout_corpus_manifest.json"
DEFAULT_FREEZE = REPO_ROOT / "research" / "implementation_freeze.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head(path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _verify_freeze(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(
            f"Held-out corpus is sealed until an implementation freeze exists: {path}"
        )
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if freeze.get("status") != "frozen":
        raise ValueError("Implementation freeze status must be 'frozen'")
    expected = freeze.get("git_commit")
    actual = _git_head(REPO_ROOT)
    if not expected or expected != actual:
        raise ValueError(
            f"Implementation freeze commit mismatch: expected={expected!r} actual={actual!r}"
        )
    return freeze


def _verify_source_checkout(source: Path, project: dict) -> None:
    if not (source / ".git").exists():
        raise ValueError(f"{source} is not a Git checkout")
    actual = _git_head(source)
    if actual != project["revision"]:
        raise ValueError(
            f"{project['name']} revision mismatch: "
            f"expected={project['revision']} actual={actual}"
        )
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    )
    if status.stdout.strip():
        raise ValueError(f"{project['name']} source checkout is dirty")


def prepare(
    source_root: Path,
    output: Path,
    manifest_path: Path = DEFAULT_MANIFEST,
    freeze_path: Path = DEFAULT_FREEZE,
) -> dict:
    freeze = _verify_freeze(freeze_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="safemap-heldout-", dir=output.parent
    ) as temporary:
        stage = Path(temporary) / output.name
        projects_root = stage / "projects"
        projects_root.mkdir(parents=True)
        copied_projects = []

        for project in manifest["projects"]:
            source = (source_root / project["name"]).resolve()
            _verify_source_checkout(source, project)
            destination = projects_root / project["name"]
            destination.mkdir()
            copied_files = []
            for item in project["files"]:
                source_file = source / item["path"]
                if not source_file.is_file():
                    raise FileNotFoundError(source_file)
                actual_hash = _sha256(source_file)
                if actual_hash != item["sha256"]:
                    raise ValueError(
                        f"{project['name']}/{item['path']} hash mismatch: "
                        f"expected={item['sha256']} actual={actual_hash}"
                    )
                destination_file = destination / item["path"]
                destination_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_file, destination_file)
                copied_files.append({**item, "copied_sha256": _sha256(destination_file)})
            (destination / "source_metadata.json").write_text(
                json.dumps(
                    {
                        "name": project["name"],
                        "repository": project["repository"],
                        "revision": project["revision"],
                        "license": project["license"],
                        "files": copied_files,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            copied_projects.append(project["name"])

        prepared_manifest = {
            **manifest,
            "execution_status": "prepared_after_implementation_freeze",
            "freeze_git_commit": freeze["git_commit"],
            "prepared_projects": copied_projects,
        }
        (stage / "manifest.json").write_text(
            json.dumps(prepared_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if output.exists():
            raise FileExistsError(
                f"Refusing to replace existing held-out corpus: {output}"
            )
        stage.replace(output)
    return prepared_manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize the sealed conference held-out corpus after an exact "
            "implementation freeze."
        )
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        required=True,
        help="Directory containing pinned checkouts named inih, cjson, and libcsv.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("external_corpus/conference_heldout"),
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--freeze-record", type=Path, default=DEFAULT_FREEZE)
    args = parser.parse_args()
    prepared = prepare(
        args.source_root,
        args.output,
        manifest_path=args.manifest,
        freeze_path=args.freeze_record,
    )
    print(
        f"prepared {len(prepared['prepared_projects'])} held-out projects at "
        f"{args.output.resolve()}"
    )


if __name__ == "__main__":
    main()

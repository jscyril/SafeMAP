from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

try:
    import typer
except ImportError:  # pragma: no cover
    typer = None

from .analysis.rust_analyzer import analyze_rust_path
from .artifacts import ArtifactStore
from .benchmarks.benchmark_runner import run_benchmarks
from .config import load_config
from .ingestion.project_loader import ingest_project
from .pipeline import (
    analyze_c_stage, plan_stage, repair_stage, report_stage, rewrite_stage,
    run_pipeline,
)
from .translation.c2rust_runner import run_c2rust
from .validation.validator import validate_project

if typer:
    app = typer.Typer(help="Analysis-guided C-to-Rust migration research prototype.")

    @app.command()
    def ingest(
        input: Path = typer.Option(..., exists=True),
        output: Path = typer.Option(...),
    ) -> None:
        store = ArtifactStore(output)
        project = ingest_project(input, store)
        typer.echo(project.to_json())

    @app.command("analyze-c")
    def analyze_c(workdir: Path = typer.Option(..., exists=True)) -> None:
        typer.echo(analyze_c_stage(ArtifactStore(workdir)).to_json())

    @app.command("translate-baseline")
    def translate_baseline(workdir: Path = typer.Option(..., exists=True)) -> None:
        store = ArtifactStore(workdir)
        typer.echo(run_c2rust(_project(store), store).to_json())

    @app.command("analyze-rust")
    def analyze_rust(
        workdir: Path = typer.Option(..., exists=True),
        rust_path: Optional[Path] = typer.Option(None),
    ) -> None:
        store = ArtifactStore(workdir)
        target = rust_path or store.path("baseline/rust")
        result = analyze_rust_path(target)
        store.write_json("analysis/baseline_rust.json", result)
        typer.echo(result.to_json())

    @app.command("plan")
    def plan_command(workdir: Path = typer.Option(..., exists=True)) -> None:
        typer.echo(json.dumps(
            [item.to_dict() for item in plan_stage(ArtifactStore(workdir))],
            indent=2,
        ))

    @app.command()
    def rewrite(
        workdir: Path = typer.Option(..., exists=True),
        config: Optional[Path] = typer.Option(None, exists=True),
    ) -> None:
        result = rewrite_stage(ArtifactStore(workdir), load_config(config))
        typer.echo(result.to_json())

    @app.command()
    def repair(
        workdir: Path = typer.Option(..., exists=True),
        config: Optional[Path] = typer.Option(None, exists=True),
    ) -> None:
        result = repair_stage(ArtifactStore(workdir), load_config(config))
        typer.echo(json.dumps(result, indent=2))

    @app.command()
    def validate(
        workdir: Path = typer.Option(..., exists=True),
        config: Optional[Path] = typer.Option(None),
    ) -> None:
        store = ArtifactStore(workdir)
        target = store.path("final/rust")
        result = validate_project(target, load_config(config).validation)
        store.write_json("validation/results.json", result)
        typer.echo(result.to_json())

    @app.command()
    def report(workdir: Path = typer.Option(..., exists=True)) -> None:
        typer.echo(report_stage(ArtifactStore(workdir)).to_json())

    @app.command("run")
    def run_command(
        input: Optional[Path] = typer.Option(None, exists=True),
        output: Path = typer.Option(Path(".")),
        config: Optional[Path] = typer.Option(None, exists=True),
    ) -> None:
        settings = load_config(config)
        selected = input or (Path(settings.project.input) if settings.project.input else None)
        if selected is None:
            raise typer.BadParameter("--input or project.input in config is required")
        store = run_pipeline(selected, output, settings)
        typer.echo(str(store.root))

    @app.command()
    def benchmark(
        benchmarks: Path = typer.Option(..., exists=True),
        output: Path = typer.Option(...),
        config: Optional[Path] = typer.Option(None, exists=True),
    ) -> None:
        rows = run_benchmarks(benchmarks, output, load_config(config))
        typer.echo(json.dumps(rows, indent=2))


def _project(store: ArtifactStore):
    from .models import ProjectInfo, from_dict
    return from_dict(ProjectInfo, store.read_json("project.json"))


def main() -> None:
    if typer is None:
        _argparse_main()
        return
    app()


def _argparse_main() -> None:  # pragma: no cover - used in minimal installations
    import argparse
    parser = argparse.ArgumentParser(
        prog="safemap",
        description="Analysis-guided C-to-Rust migration research prototype.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("--input", required=True)
    ingest_parser.add_argument("--output", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--input")
    run_parser.add_argument("--output", default=".")
    run_parser.add_argument("--config")
    benchmark_parser = subparsers.add_parser("benchmark")
    benchmark_parser.add_argument("--benchmarks", required=True)
    benchmark_parser.add_argument("--output", required=True)
    benchmark_parser.add_argument("--config")
    for command in ("analyze-c", "translate-baseline", "analyze-rust", "plan", "rewrite", "repair", "validate", "report"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--workdir", required=True)
        if command in {"rewrite", "repair", "validate"}:
            command_parser.add_argument("--config")
    args = parser.parse_args()
    if args.command == "ingest":
        project = ingest_project(args.input, ArtifactStore(Path(args.output)))
        print(project.to_json())
    elif args.command == "run":
        settings = load_config(args.config)
        selected = args.input or settings.project.input
        if not selected:
            parser.error("run requires --input or project.input in config")
        print(run_pipeline(selected, args.output, settings).root)
    elif args.command == "benchmark":
        print(json.dumps(run_benchmarks(
            Path(args.benchmarks), Path(args.output), load_config(args.config)
        ), indent=2))
    else:
        store = ArtifactStore(Path(args.workdir))
        if args.command == "analyze-c":
            print(analyze_c_stage(store).to_json())
        elif args.command == "translate-baseline":
            print(run_c2rust(_project(store), store).to_json())
        elif args.command == "analyze-rust":
            print(analyze_rust_path(store.path("baseline/rust")).to_json())
        elif args.command == "plan":
            print(json.dumps([item.to_dict() for item in plan_stage(store)], indent=2))
        elif args.command == "rewrite":
            print(rewrite_stage(store, load_config(args.config)).to_json())
        elif args.command == "repair":
            print(json.dumps(repair_stage(store, load_config(args.config)), indent=2))
        elif args.command == "validate":
            print(validate_project(
                store.path("final/rust"), load_config(args.config).validation
            ).to_json())
        elif args.command == "report":
            print(report_stage(store).to_json())


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

try:
    import typer
except ImportError:  # pragma: no cover
    typer = None

from .analysis.rust_analyzer import analyze_rust_path
from .artifacts import ArtifactStore
from .benchmarks.benchmark_runner import (
    dry_run_benchmarks, export_combined_evaluation, export_latex_tables,
    export_paper_tables, publication_metric_summary, run_benchmarks,
    run_final_evaluation, write_artifact_metadata,
)
from .config import load_config
from .ingestion.project_loader import ingest_project
from .pipeline import (
    analyze_c_stage, plan_stage, repair_stage, report_stage, rewrite_stage,
    run_pipeline,
)
from .runs import latest_run, summarize_runs
from .translation.c2rust_runner import run_c2rust
from .validation.validator import validate_project

BENCHMARK_MODE_HELP = (
    "Repeat to select modes: c2rust_only, llm_only, "
    "c2rust_llm_unguided, safemap_no_static_guidance, "
    "safemap_deterministic, safemap_full."
)

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
        mode: list[str] = typer.Option(None, help=BENCHMARK_MODE_HELP),
        dry_run: bool = typer.Option(
            False,
            help="Validate inputs, modes, tools, API-key status, and output reuse.",
        ),
    ) -> None:
        settings = load_config(config)
        if dry_run:
            typer.echo(json.dumps(
                dry_run_benchmarks(benchmarks, output, settings, modes=mode),
                indent=2,
            ))
            return
        _echo_warnings(dry_run_benchmarks(benchmarks, output, settings, modes=mode))
        rows = run_benchmarks(benchmarks, output, settings, modes=mode)
        typer.echo(json.dumps(rows, indent=2))

    @app.command("export-tables")
    def export_tables(
        input: Path = typer.Option(..., exists=True),
        output: Path = typer.Option(...),
    ) -> None:
        export_paper_tables(input, output)
        typer.echo(str(output))

    @app.command("export-latex-tables")
    def export_latex_tables_command(
        input: Path = typer.Option(..., exists=True),
        output: Path = typer.Option(...),
    ) -> None:
        export_latex_tables(input, output)
        typer.echo(str(output))

    @app.command("combined-eval")
    def combined_eval(
        output: Path = typer.Option(Path("reports/combined_evaluation.md")),
        main_csv: Path = typer.Option(Path("reports/final/benchmark_results.csv")),
        case_study_csv: Optional[Path] = typer.Option(
            Path("reports/case-studies/benchmark_results.csv")
        ),
        external_csv: Optional[Path] = typer.Option(None),
        c2rust_csv: Optional[Path] = typer.Option(None),
        ablation_csv: Optional[Path] = typer.Option(None),
        llm_smoke_csv: Optional[Path] = typer.Option(None),
        allow_denominator_mismatch: bool = typer.Option(False),
    ) -> None:
        export_combined_evaluation(
            output,
            main_csv,
            case_study_csv=case_study_csv,
            external_csv=external_csv,
            c2rust_csv=c2rust_csv,
            ablation_csv=ablation_csv,
            llm_smoke_csv=llm_smoke_csv,
            allow_denominator_mismatch=allow_denominator_mismatch,
        )
        typer.echo(str(output))

    @app.command("artifact-metadata")
    def artifact_metadata(
        output: Path = typer.Option(Path("reports/artifact_metadata.json")),
    ) -> None:
        typer.echo(json.dumps(write_artifact_metadata(output), indent=2))

    @app.command("metric-summary")
    def metric_summary(
        main_csv: Path = typer.Option(
            Path("reports/final/benchmark_results.csv"), exists=True
        ),
        case_study_csv: Optional[Path] = typer.Option(
            Path("reports/case-studies/benchmark_results.csv")
        ),
        external_csv: Optional[Path] = typer.Option(
            Path("reports/external-corpus/benchmark_results.csv")
        ),
        c2rust_csv: Optional[Path] = typer.Option(
            Path("reports/c2rust-only/benchmark_results.csv")
        ),
        ablation_csv: Optional[Path] = typer.Option(
            Path("reports/ablation/benchmark_results.csv")
        ),
        llm_subset_csv: Optional[Path] = typer.Option(None),
    ) -> None:
        typer.echo(publication_metric_summary(
            main_csv,
            case_study_csv=case_study_csv,
            external_csv=external_csv,
            c2rust_csv=c2rust_csv,
            ablation_csv=ablation_csv,
            llm_subset_csv=llm_subset_csv,
        ))

    @app.command("latest-run")
    def latest_run_command(
        output: Path = typer.Option(Path(".")),
    ) -> None:
        run = latest_run(output)
        if run is None:
            raise typer.BadParameter(f"No SafeMAP runs found under {output}")
        typer.echo(str(run))

    @app.command("summarize-runs")
    def summarize_runs_command(
        output: Path = typer.Option(Path(".")),
    ) -> None:
        typer.echo(json.dumps(summarize_runs(output), indent=2))

    @app.command("final-eval")
    def final_eval(
        benchmarks: Path = typer.Option(Path("examples"), exists=True),
        output: Path = typer.Option(Path("reports/final")),
        config: Optional[Path] = typer.Option(None, exists=True),
        mode: list[str] = typer.Option(None, help=BENCHMARK_MODE_HELP),
        dry_run: bool = typer.Option(
            False,
            help="Validate inputs, modes, tools, API-key status, and output reuse.",
        ),
    ) -> None:
        settings = load_config(config)
        if dry_run:
            typer.echo(json.dumps(
                dry_run_benchmarks(benchmarks, output, settings, modes=mode),
                indent=2,
            ))
            return
        _echo_warnings(dry_run_benchmarks(benchmarks, output, settings, modes=mode))
        manifest = run_final_evaluation(
            benchmarks, output, settings, modes=mode
        )
        typer.echo(json.dumps(manifest, indent=2))


def _project(store: ArtifactStore):
    from .models import ProjectInfo, from_dict
    return from_dict(ProjectInfo, store.read_json("project.json"))


def main() -> None:
    if typer is None:
        _argparse_main()
        return
    app()


def _echo_warnings(preflight: dict[str, object]) -> None:
    for warning in preflight.get("warnings", []):
        if typer:
            typer.echo(f"warning: {warning}", err=True)
        else:
            print(f"warning: {warning}", file=sys.stderr)


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
    benchmark_parser.add_argument(
        "--mode", action="append", help=BENCHMARK_MODE_HELP
    )
    benchmark_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs, modes, tools, API-key status, and output reuse.",
    )
    export_parser = subparsers.add_parser("export-tables")
    export_parser.add_argument("--input", required=True)
    export_parser.add_argument("--output", required=True)
    latex_parser = subparsers.add_parser("export-latex-tables")
    latex_parser.add_argument("--input", required=True)
    latex_parser.add_argument("--output", required=True)
    combined_parser = subparsers.add_parser("combined-eval")
    combined_parser.add_argument("--output", default="reports/combined_evaluation.md")
    combined_parser.add_argument(
        "--main-csv", default="reports/final/benchmark_results.csv"
    )
    combined_parser.add_argument(
        "--case-study-csv", default="reports/case-studies/benchmark_results.csv"
    )
    combined_parser.add_argument("--external-csv")
    combined_parser.add_argument("--c2rust-csv")
    combined_parser.add_argument("--ablation-csv")
    combined_parser.add_argument("--llm-smoke-csv")
    combined_parser.add_argument("--allow-denominator-mismatch", action="store_true")
    metadata_parser = subparsers.add_parser("artifact-metadata")
    metadata_parser.add_argument("--output", default="reports/artifact_metadata.json")
    metric_parser = subparsers.add_parser("metric-summary")
    metric_parser.add_argument("--main-csv", default="reports/final/benchmark_results.csv")
    metric_parser.add_argument(
        "--case-study-csv", default="reports/case-studies/benchmark_results.csv"
    )
    metric_parser.add_argument("--external-csv")
    metric_parser.add_argument(
        "--c2rust-csv", default="reports/c2rust-only/benchmark_results.csv"
    )
    metric_parser.add_argument("--ablation-csv")
    metric_parser.add_argument("--llm-subset-csv")
    latest_parser = subparsers.add_parser("latest-run")
    latest_parser.add_argument("--output", default=".")
    summarize_parser = subparsers.add_parser("summarize-runs")
    summarize_parser.add_argument("--output", default=".")
    final_parser = subparsers.add_parser("final-eval")
    final_parser.add_argument("--benchmarks", default="examples")
    final_parser.add_argument("--output", default="reports/final")
    final_parser.add_argument("--config")
    final_parser.add_argument("--mode", action="append", help=BENCHMARK_MODE_HELP)
    final_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs, modes, tools, API-key status, and output reuse.",
    )
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
        settings = load_config(args.config)
        if args.dry_run:
            print(json.dumps(dry_run_benchmarks(
                Path(args.benchmarks), Path(args.output), settings,
                modes=args.mode,
            ), indent=2))
            return
        _echo_warnings(dry_run_benchmarks(
            Path(args.benchmarks), Path(args.output), settings,
            modes=args.mode,
        ))
        print(json.dumps(run_benchmarks(
            Path(args.benchmarks), Path(args.output), settings,
            modes=args.mode,
        ), indent=2))
    elif args.command == "export-tables":
        export_paper_tables(Path(args.input), Path(args.output))
        print(args.output)
    elif args.command == "export-latex-tables":
        export_latex_tables(Path(args.input), Path(args.output))
        print(args.output)
    elif args.command == "combined-eval":
        export_combined_evaluation(
            Path(args.output),
            Path(args.main_csv),
            case_study_csv=Path(args.case_study_csv)
            if args.case_study_csv else None,
            external_csv=Path(args.external_csv)
            if args.external_csv else None,
            c2rust_csv=Path(args.c2rust_csv) if args.c2rust_csv else None,
            ablation_csv=Path(args.ablation_csv)
            if args.ablation_csv else None,
            llm_smoke_csv=Path(args.llm_smoke_csv) if args.llm_smoke_csv else None,
            allow_denominator_mismatch=args.allow_denominator_mismatch,
        )
        print(args.output)
    elif args.command == "artifact-metadata":
        print(json.dumps(write_artifact_metadata(Path(args.output)), indent=2))
    elif args.command == "metric-summary":
        print(publication_metric_summary(
            Path(args.main_csv),
            case_study_csv=Path(args.case_study_csv)
            if args.case_study_csv else None,
            external_csv=Path(args.external_csv)
            if args.external_csv else None,
            c2rust_csv=Path(args.c2rust_csv) if args.c2rust_csv else None,
            ablation_csv=Path(args.ablation_csv)
            if args.ablation_csv else None,
            llm_subset_csv=Path(args.llm_subset_csv)
            if args.llm_subset_csv else None,
        ), end="")
    elif args.command == "latest-run":
        run = latest_run(Path(args.output))
        if run is None:
            parser.error(f"No SafeMAP runs found under {args.output}")
        print(run)
    elif args.command == "summarize-runs":
        print(json.dumps(summarize_runs(Path(args.output)), indent=2))
    elif args.command == "final-eval":
        settings = load_config(args.config)
        if args.dry_run:
            print(json.dumps(dry_run_benchmarks(
                Path(args.benchmarks), Path(args.output), settings,
                modes=args.mode,
            ), indent=2))
            return
        _echo_warnings(dry_run_benchmarks(
            Path(args.benchmarks), Path(args.output), settings,
            modes=args.mode,
        ))
        print(json.dumps(run_final_evaluation(
            Path(args.benchmarks), Path(args.output), settings,
            modes=args.mode,
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

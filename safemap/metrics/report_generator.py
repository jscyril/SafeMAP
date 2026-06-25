from __future__ import annotations

import csv
from io import StringIO

from ..models import RunMetrics, RustMetrics


def percentage_reduction(before: int, after: int) -> float | None:
    if before == 0:
        return None
    return round((before - after) / before * 100.0, 2)


def generate_markdown(metrics: RunMetrics) -> str:
    before = metrics.baseline
    after = metrics.safemap
    rows = [
        ("Unsafe blocks", _value(before, "unsafe_blocks"), _value(after, "unsafe_blocks")),
        ("Unsafe functions", _value(before, "unsafe_functions"), _value(after, "unsafe_functions")),
        ("Raw pointer types", _value(before, "raw_pointer_types"), _value(after, "raw_pointer_types")),
        ("Raw pointer dereferences", _value(before, "raw_pointer_dereferences"), _value(after, "raw_pointer_dereferences")),
        ("Unsafe lines", _value(before, "unsafe_lines"), _value(after, "unsafe_lines")),
    ]
    table = [
        "| Metric | C2Rust Baseline | SafeMAP | Improvement |",
        "|---|---:|---:|---:|",
    ]
    for label, old, new in rows:
        reduction = (
            percentage_reduction(old, new)
            if isinstance(old, int) and isinstance(new, int) else None
        )
        improvement = "N/A" if reduction is None else f"{reduction:.2f}%"
        table.append(f"| {label} | {old} | {new} | {improvement} |")
    failed = "\n".join(
        f"- `{item.get('unit_id', 'unknown')}`: {item.get('reason', 'unknown')}"
        for item in metrics.failed_units
    ) or "None."
    residual = "\n".join(
        f"- `{item.get('location', 'unknown')}`: {item.get('category', 'unknown')} - "
        f"{item.get('reason', '')}"
        for item in metrics.residual_unsafe
    ) or "None."
    idioms = "\n".join(
        f"- `{name}`: {count}" for name, count in sorted(metrics.migrated_idioms.items())
    ) or "None."
    eligibility = "\n".join(
        f"- `{name}`: {count}" for name, count in sorted(metrics.eligibility_counts.items())
    ) or "None."
    accepted = "\n".join(
        f"- `{unit_id}`" for unit_id in metrics.fully_safe_accepted_unit_ids
    ) or "None."
    failures = "\n".join(
        f"- `{name}`: {count}" for name, count in sorted(metrics.failure_categories.items())
    ) or "None."
    return (
        "# SafeMAP Migration Report\n\n"
        "## Project Summary\n\n"
        f"Project: `{metrics.project}`\n\n"
        f"Total translation units: `{metrics.total_units}`\n\n"
        f"Eligible units: `{metrics.eligible_units}`\n\n"
        f"Fully safe accepted units: `{metrics.fully_safe_accepted_units}`\n\n"
        "Fully safe translation unit acceptance rate: "
        f"`{metrics.fully_safe_translation_unit_acceptance_rate}`\n\n"
        "## Eligibility Classification\n\n" + eligibility + "\n\n"
        "## Baseline Results\n\n"
        f"Compilation: `{metrics.baseline_compile}`\n\n"
        "## SafeMAP Results\n\n"
        f"Compilation: `{metrics.safemap_compile}`\n\n"
        "SafeMAP accepts a unit only when the generated Rust compiles with "
        "`#![forbid(unsafe_code)]`, has no unsafe constructs, exposes no raw-pointer "
        "public API, and passes available validation.\n\n"
        "## Comparison\n\n"
        + "\n".join(table)
        + "\n\n## Fully Safe Accepted Units\n\n" + accepted
        + "\n\n## Migrated Idioms\n\n" + idioms
        + "\n\n## Failure Categories\n\n" + failures
        + "\n\n## Remaining Unsafe Code\n\n" + residual
        + "\n\n## Validation Results\n\n"
        f"Test pass rate: `{metrics.test_pass_rate}`\n\n"
        f"Differential pass rate: `{metrics.differential_pass_rate}`\n\n"
        "## Failed Units\n\n" + failed
        + "\n\n## Recommendations for Manual Review\n\n"
        "Review failed translation units and every residual unsafe classification.\n"
    )


def comparison_csv(metrics: RunMetrics) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "unit_id", "baseline", "eligibility", "generated", "compile_status",
        "test_status", "differential_status", "unsafe_blocks", "raw_pointers",
        "fully_safe_accepted", "failure_reason",
    ])
    if metrics.total_units:
        accepted = set(metrics.fully_safe_accepted_unit_ids)
        failed = {item.get("unit_id", ""): item.get("reason", "") for item in metrics.failed_units}
        for index in range(metrics.total_units):
            unit_id = f"unit_{index}"
            writer.writerow([
                unit_id,
                "c2rust_baseline" if metrics.baseline is not None else "skipped",
                "",
                "safemap_final" if metrics.safemap is not None else "skipped",
                metrics.safemap_compile,
                metrics.test_pass_rate,
                metrics.differential_pass_rate,
                _value(metrics.safemap, "unsafe_blocks", ""),
                _value(metrics.safemap, "raw_pointer_types", ""),
                unit_id in accepted,
                failed.get(unit_id, ""),
            ])
        return output.getvalue()
    writer.writerow(["metric", "c2rust_baseline", "safemap", "", "", "", "", "", "", "", ""])
    for name in ("unsafe_blocks", "unsafe_functions", "raw_pointer_types", "unsafe_lines"):
        writer.writerow([
            name,
            _value(metrics.baseline, name, ""),
            _value(metrics.safemap, name, ""),
        ])
    return output.getvalue()


def _value(metrics: RustMetrics | None, name: str, unavailable: str = "N/A"):
    return getattr(metrics, name) if metrics is not None else unavailable

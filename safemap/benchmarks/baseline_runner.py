from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineMode:
    name: str
    use_c2rust: bool
    use_llm: bool
    guided: bool
    disabled_components: tuple[str, ...] = ()


BASELINES = (
    BaselineMode("c2rust_only", True, False, False),
    BaselineMode("llm_only", False, True, False),
    BaselineMode("c2rust_llm_unguided", True, True, False),
    BaselineMode("safemap_no_static_guidance", False, False, False),
    BaselineMode("safemap_deterministic", False, False, True),
    BaselineMode(
        "safemap_without_pointer_roles",
        False,
        False,
        True,
        ("pointer_roles",),
    ),
    BaselineMode(
        "safemap_without_safe_signatures",
        False,
        False,
        True,
        ("safe_signatures",),
    ),
    BaselineMode(
        "safemap_without_dependency_grouping",
        False,
        False,
        True,
        ("dependency_grouping",),
    ),
    BaselineMode(
        "safemap_without_idiom_plans",
        False,
        False,
        True,
        ("idiom_plans",),
    ),
    BaselineMode(
        "safemap_without_validation_feedback",
        False,
        False,
        True,
        ("validation_feedback",),
    ),
    BaselineMode("safemap_full", True, True, True),
)

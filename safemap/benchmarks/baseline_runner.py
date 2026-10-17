from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineMode:
    name: str
    use_c2rust: bool
    use_llm: bool
    guided: bool
    disabled_components: tuple[str, ...] = ()
    engine: str = "legacy"
    prompt_guidance: bool = True


COMPONENTS = (
    "pointer_roles",
    "safe_signatures",
    "dependency_grouping",
    "idiom_plans",
    "validation_feedback",
)

BASELINES = (
    BaselineMode("c2rust_only", True, False, False),
    BaselineMode("llm_only", False, True, False),
    BaselineMode("c2rust_llm_unguided", True, True, False),
    BaselineMode("safemap_no_static_guidance", False, False, False),
    # Deterministic rules only, with per-unit acceptance.
    BaselineMode("safemap_deterministic", False, False, True, engine="unit"),
    *(
        BaselineMode(
            f"safemap_without_{component}", False, False, True, (component,),
            engine="unit",
        )
        for component in COMPONENTS
    ),
    # Primary configuration: analysis-guided plans, rules first, then
    # plan-guided LLM synthesis with compiler-feedback repair.
    BaselineMode("safemap_guided", False, True, True, engine="unit"),
    # Same loop and signatures, but analysis facts and plans withheld.
    BaselineMode(
        "safemap_guided_unguided_prompt", False, True, True,
        engine="unit", prompt_guidance=False,
    ),
    *(
        BaselineMode(
            f"safemap_guided_without_{component}", False, True, True, (component,),
            engine="unit",
        )
        for component in COMPONENTS
    ),
    BaselineMode("safemap_full", True, True, True),
)

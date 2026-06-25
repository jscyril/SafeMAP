from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineMode:
    name: str
    use_c2rust: bool
    use_llm: bool
    guided: bool


BASELINES = (
    BaselineMode("c2rust_only", True, False, False),
    BaselineMode("llm_only", False, True, False),
    BaselineMode("c2rust_llm_unguided", True, True, False),
    BaselineMode("safemap_full", True, True, True),
)


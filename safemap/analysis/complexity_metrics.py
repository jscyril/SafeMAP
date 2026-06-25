from __future__ import annotations

import re


def cyclomatic_complexity(source: str) -> int:
    return 1 + len(re.findall(r"\b(?:if|for|while|case)\b|&&|\|\||\?", source))


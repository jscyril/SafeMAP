from __future__ import annotations

from ..models import CAnalysis


def build_call_graph(analysis: CAnalysis) -> dict[str, set[str]]:
    known = {function.name for function in analysis.functions}
    return {
        function.name: set(function.calls).intersection(known)
        for function in analysis.functions
    }


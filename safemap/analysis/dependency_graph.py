from __future__ import annotations

from .call_graph import build_call_graph
from ..models import CAnalysis, TranslationUnit


def create_translation_units(analysis: CAnalysis) -> list[TranslationUnit]:
    graph = build_call_graph(analysis)
    components = strongly_connected_components(graph)
    owner = {name: index for index, group in enumerate(components) for name in group}
    units = []
    by_name = {function.name: function for function in analysis.functions}
    for index, members in enumerate(components):
        dependencies = sorted({
            f"unit_{owner[dependency]}"
            for member in members
            for dependency in graph.get(member, set())
            if owner[dependency] != index
        })
        functions = [by_name[name] for name in members]
        idioms = sorted({
            idiom.idiom_type for function in functions for idiom in function.idioms
        })
        unsafe_weight = sum(len(function.pointer_facts) for function in functions)
        priority = min(1.0, 0.2 + 0.12 * unsafe_weight + 0.08 * len(idioms))
        units.append(TranslationUnit(
            unit_id=f"unit_{index}",
            kind="recursive_group" if len(members) > 1 else "function",
            c_function=members[0],
            rust_function=members[0],
            dependencies=dependencies,
            priority=round(priority, 3),
            reason=", ".join(idioms) if idioms else "dependency-ordered function",
            members=sorted(members),
        ))
    return _topological_units(units)


def strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    result: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in indices:
                visit(neighbor)
                lowlink[node] = min(lowlink[node], lowlink[neighbor])
            elif neighbor in on_stack:
                lowlink[node] = min(lowlink[node], indices[neighbor])
        if lowlink[node] == indices[node]:
            component = []
            while True:
                item = stack.pop()
                on_stack.remove(item)
                component.append(item)
                if item == node:
                    break
            result.append(sorted(component))

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return result


def _topological_units(units: list[TranslationUnit]) -> list[TranslationUnit]:
    remaining = {unit.unit_id: unit for unit in units}
    ordered = []
    while remaining:
        ready = sorted(
            (
                unit for unit in remaining.values()
                if not set(unit.dependencies).intersection(remaining)
            ),
            key=lambda unit: (-unit.priority, unit.unit_id),
        )
        if not ready:
            ready = [remaining[sorted(remaining)[0]]]
        for unit in ready:
            ordered.append(unit)
            remaining.pop(unit.unit_id)
    return ordered


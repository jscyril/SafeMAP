from safemap.analysis.dependency_graph import create_translation_units, strongly_connected_components
from safemap.models import CAnalysis, FunctionInfo


def function(name: str, calls: list[str]) -> FunctionInfo:
    return FunctionInfo(name, "int", [], "", "x.c", 1, 1, calls=calls)


def test_groups_cycles_and_orders_dependencies() -> None:
    analysis = CAnalysis(functions=[
        function("caller", ["left"]),
        function("left", ["right"]),
        function("right", ["left"]),
    ])
    units = create_translation_units(analysis)
    assert units[0].members == ["left", "right"]
    assert units[1].members == ["caller"]


def test_strong_components_include_isolated_nodes() -> None:
    result = strongly_connected_components({"a": set(), "b": {"b"}})
    assert sorted(result) == [["a"], ["b"]]


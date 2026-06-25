from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import (
    CAnalysis, FunctionInfo, GlobalInfo, ParameterInfo, ProjectInfo, StructInfo,
)
from .idiom_detector import detect_idioms
from .pointer_classifier import classify_pointers

try:
    from clang import cindex
except ImportError:  # pragma: no cover - optional dependency
    cindex = None


def analyze_c_project(project: ProjectInfo) -> CAnalysis:
    if cindex is not None:
        try:
            return _analyze_with_clang(project)
        except Exception as error:
            fallback = _analyze_fallback(project)
            fallback.diagnostics.insert(0, f"libclang unavailable at runtime: {error}")
            return fallback
    fallback = _analyze_fallback(project)
    fallback.diagnostics.insert(0, "Python clang bindings are not installed")
    return fallback


def _analyze_with_clang(project: ProjectInfo) -> CAnalysis:
    arguments = _compile_arguments(project)
    analysis = CAnalysis()
    index = cindex.Index.create()
    for file_name in project.c_files:
        args = arguments.get(str(Path(file_name).resolve()), [])
        unit = index.parse(file_name, args=args)
        analysis.diagnostics.extend(str(item) for item in unit.diagnostics)
        source = Path(file_name).read_text(encoding="utf-8", errors="replace")
        _walk_clang(unit.cursor, Path(file_name), source, analysis)
    _enrich_functions(analysis.functions)
    return analysis


def _compile_arguments(project: ProjectInfo) -> dict[str, list[str]]:
    if not project.compile_commands:
        return {}
    data = json.loads(Path(project.compile_commands).read_text(encoding="utf-8"))
    result = {}
    for item in data:
        args = list(item.get("arguments", []))
        if not args and item.get("command"):
            import shlex
            args = shlex.split(item["command"])
        if args:
            args = args[1:]
        result[str(Path(item["file"]).resolve())] = [
            arg for arg in args if arg not in {"-c", item["file"]}
            and not arg.startswith("-o")
        ]
    return result


def _walk_clang(cursor, file_path: Path, source: str, analysis: CAnalysis) -> None:
    kinds = cindex.CursorKind
    for child in cursor.get_children():
        location = child.location
        if not location.file or Path(location.file.name).resolve() != file_path.resolve():
            continue
        if child.kind == kinds.FUNCTION_DECL and child.is_definition():
            start, end = child.extent.start, child.extent.end
            body = _source_extent(source, start.offset, end.offset)
            params = [
                ParameterInfo(
                    name=argument.spelling,
                    c_type=argument.type.spelling,
                    is_pointer=argument.type.kind == cindex.TypeKind.POINTER,
                    is_const=(
                        argument.type.kind == cindex.TypeKind.POINTER
                        and argument.type.get_pointee().is_const_qualified()
                    ),
                )
                for argument in child.get_arguments()
            ]
            calls = sorted({
                node.spelling for node in _descendants(child)
                if node.kind == kinds.CALL_EXPR and node.spelling
            })
            analysis.functions.append(FunctionInfo(
                name=child.spelling,
                return_type=child.result_type.spelling,
                parameters=params,
                body=body,
                file=str(file_path),
                start_line=start.line,
                end_line=end.line,
                calls=calls,
            ))
        elif child.kind == kinds.STRUCT_DECL and child.is_definition() and child.spelling:
            fields = [
                {"name": field.spelling, "type": field.type.spelling}
                for field in child.get_children()
                if field.kind == kinds.FIELD_DECL
            ]
            analysis.structs.append(StructInfo(
                child.spelling, fields, str(file_path), location.line
            ))
        elif child.kind == kinds.VAR_DECL and child.semantic_parent.kind == kinds.TRANSLATION_UNIT:
            analysis.globals.append(GlobalInfo(
                name=child.spelling,
                c_type=child.type.spelling,
                mutable=not child.type.is_const_qualified(),
                file=str(file_path),
                line=location.line,
            ))


def _descendants(cursor):
    for child in cursor.get_children():
        yield child
        yield from _descendants(child)


def _source_extent(source: str, start: int, end: int) -> str:
    raw = source.encode("utf-8")
    return raw[start:end].decode("utf-8", errors="replace")


def _analyze_fallback(project: ProjectInfo) -> CAnalysis:
    analysis = CAnalysis()
    for file_name in project.c_files:
        path = Path(file_name)
        source = path.read_text(encoding="utf-8", errors="replace")
        analysis.functions.extend(_fallback_functions(path, source))
        analysis.structs.extend(_fallback_structs(path, source))
    _enrich_functions(analysis.functions)
    return analysis


FUNCTION_HEADER = re.compile(
    r"(?m)^[ \t]*(?!if\b|for\b|while\b|switch\b)"
    r"(?P<return>(?:[A-Za-z_]\w*[\s*]+)+?)"
    r"(?P<name>[A-Za-z_]\w*)\s*\((?P<params>[^;{}]*)\)\s*\{"
)


def _fallback_functions(path: Path, source: str) -> list[FunctionInfo]:
    functions = []
    for match in FUNCTION_HEADER.finditer(source):
        end = _matching_brace(source, source.find("{", match.start()))
        if end is None:
            continue
        params = _parse_parameters(match.group("params"))
        body = source[match.start():end + 1]
        calls = sorted({
            name for name in re.findall(r"\b([A-Za-z_]\w*)\s*\(", body)
            if name not in {"if", "for", "while", "switch", "sizeof", match.group("name")}
        })
        functions.append(FunctionInfo(
            name=match.group("name"),
            return_type=" ".join(match.group("return").split()),
            parameters=params,
            body=body,
            file=str(path),
            start_line=source.count("\n", 0, match.start()) + 1,
            end_line=source.count("\n", 0, end) + 1,
            calls=calls,
        ))
    return functions


def _matching_brace(source: str, opening: int) -> int | None:
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return None


def _parse_parameters(raw: str) -> list[ParameterInfo]:
    if not raw.strip() or raw.strip() == "void":
        return []
    parameters = []
    for item in raw.split(","):
        item = item.strip()
        match = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?$", item)
        if not match:
            continue
        name = match.group(1)
        c_type = item[:match.start(1)].strip()
        is_array = "[" in item
        parameters.append(ParameterInfo(
            name=name,
            c_type=(c_type + " *").strip() if is_array else c_type,
            is_pointer="*" in c_type or is_array,
            is_const=bool(re.search(r"\bconst\b", c_type)),
        ))
    return parameters


def _fallback_structs(path: Path, source: str) -> list[StructInfo]:
    structs = []
    for match in re.finditer(r"\bstruct\s+([A-Za-z_]\w*)\s*\{([^}]*)\}", source, re.DOTALL):
        fields = []
        for declaration in match.group(2).split(";"):
            field = re.search(r"(.+?)\s+([A-Za-z_]\w*)\s*$", declaration.strip())
            if field:
                fields.append({"name": field.group(2), "type": field.group(1).strip()})
        structs.append(StructInfo(
            match.group(1), fields, str(path),
            source.count("\n", 0, match.start()) + 1,
        ))
    return structs


def _enrich_functions(functions: list[FunctionInfo]) -> None:
    for function in functions:
        function.pointer_facts = classify_pointers(function.parameters, function.body)
        function.idioms = detect_idioms(function)


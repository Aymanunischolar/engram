"""Structural chunking for Python source: cognee's built-in loaders treat code
files as plain text (no function/class-aware parsing), so this fills that gap
before handing chunks to cognee.add().
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path

import cognee

IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".data_storage",
    ".cognee_system",
    ".cognee_cache",
}


@dataclass
class CodeEntity:
    kind: str
    name: str
    qualified_name: str
    file_path: str
    lineno: int
    end_lineno: int
    docstring: str | None
    calls: list[str] = field(default_factory=list)
    source: str = ""

    def as_text(self) -> str:
        header = (
            f"{self.kind} `{self.qualified_name}` in {self.file_path} "
            f"(lines {self.lineno}-{self.end_lineno})"
        )
        parts = [header]
        if self.docstring:
            parts.append(f"Docstring: {self.docstring}")
        if self.calls:
            parts.append(f"Calls: {', '.join(self.calls)}")
        parts.append(f"```python\n{self.source}\n```")
        return "\n\n".join(parts)


def _extract_calls(node: ast.AST) -> list[str]:
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                calls.append(func.id)
            elif isinstance(func, ast.Attribute):
                calls.append(func.attr)
    return calls


class _EntityVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str, lines: list[str]):
        self.relative_path = relative_path
        self.lines = lines
        self.entities: list[CodeEntity] = []
        self._class_stack: list[str] = []

    def _qualified_name(self, name: str) -> str:
        scope = ".".join([*self._class_stack, name])
        return f"{self.relative_path}:{scope}"

    def _add_entity(self, kind: str, node: ast.AST) -> None:
        end = getattr(node, "end_lineno", node.lineno)
        self.entities.append(
            CodeEntity(
                kind=kind,
                name=node.name,
                qualified_name=self._qualified_name(node.name),
                file_path=self.relative_path,
                lineno=node.lineno,
                end_lineno=end,
                docstring=ast.get_docstring(node),
                calls=sorted(set(_extract_calls(node))) if kind == "function" else [],
                source="\n".join(self.lines[node.lineno - 1 : end]),
            )
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._add_entity("class", node)
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._add_entity("function", node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef


def parse_python_file(file_path: Path, repo_root: Path) -> list[CodeEntity]:
    source = file_path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    relative_path = file_path.relative_to(repo_root).as_posix()
    visitor = _EntityVisitor(relative_path, source.splitlines())
    visitor.visit(tree)
    return visitor.entities


def discover_python_files(repo_root: Path) -> list[Path]:
    return [
        path for path in repo_root.rglob("*.py") if not IGNORED_DIR_NAMES.intersection(path.parts)
    ]


def parse_repo(repo_root: Path) -> list[CodeEntity]:
    entities = []
    for file_path in discover_python_files(repo_root):
        entities.extend(parse_python_file(file_path, repo_root))
    return entities


async def ingest_repo(repo_root: Path, dataset_name: str = "main_dataset") -> int:
    entities = parse_repo(repo_root)
    chunks = [entity.as_text() for entity in entities]
    if chunks:
        await cognee.add(chunks, dataset_name=dataset_name)
    return len(chunks)

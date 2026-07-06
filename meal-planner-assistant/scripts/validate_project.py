"""
validate_project.py — Structural integrity checks for meal-planner-assistant.

Validates:
  1. Agent registration       7. Pydantic usage
  2. Tool registration        8. Folder structure
  3. Missing tests            9. Naming conventions
  4. Circular imports        10. Forbidden imports
  5. Hardcoded models        11. Dependency direction
  6. Hardcoded API keys      12. Unreferenced files

Exit code 0 = all pass, 1 = failures found.
"""

import ast
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
AGENTS_DIR = APP_DIR / "agents"
TOOLS_DIR = APP_DIR / "tools"
MODELS_DIR = APP_DIR / "models"
DATA_DIR = APP_DIR / "data"
UTILS_DIR = APP_DIR / "app_utils"
TESTS_DIR = PROJECT_ROOT / "tests"
UNIT_DIR = TESTS_DIR / "unit"
RULES_DIR = PROJECT_ROOT / ".agents" / "rules"

REQUIRED_DIRS = [
    APP_DIR,
    AGENTS_DIR,
    TOOLS_DIR,
    MODELS_DIR,
    DATA_DIR,
    TESTS_DIR,
    UNIT_DIR,
    RULES_DIR,
]

FORBIDDEN_IMPORTS = {
    "typing.Dict",
    "typing.List",
    "typing.Optional",
    "typing.Tuple",
    "typing.Set",
    "typing.Callable",
    "typing.Type",
}

# Which directories are allowed to import from which other directories
ALLOWED_DEPENDENCIES: dict[str, set[str]] = {
    "app.agents": {"app.tools", "app.data", "app.models", "google"},
    "app.tools": {"app.data", "app.models", "app", "google"},
    "app.data": {"app.models", "app"},
    "app.models": set(),
    "app.app_utils": {"app.models", "google", "a2a", "fastapi"},
}


@dataclass
class Finding:
    field: str
    severity: str  # "error" or "warning"
    message: str
    file: str = ""
    line: int = 0


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _py_files(dir_path: Path) -> list[Path]:
    if not dir_path.is_dir():
        return []
    return sorted(dir_path.glob("*.py"))


def _strip_init(filepath: Path) -> str:
    stem = filepath.stem
    return "" if stem == "__init__" else stem


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _parse_ast(path: Path) -> ast.Module | None:
    try:
        return ast.parse(_read_file(path), filename=str(path))
    except SyntaxError:
        return None


# ---------------------------------------------------------------------------
# 1. Agent registration
# ---------------------------------------------------------------------------


def check_agent_registration() -> list[Finding]:
    findings: list[Finding] = []

    agent_files = {_strip_init(p) for p in _py_files(AGENTS_DIR)}
    agent_files.discard("")

    coordinator_path = APP_DIR / "agent.py"
    coordinator_tree = _parse_ast(coordinator_path)

    registered_agents: set[str] = set()
    created_agents: set[str] = set()

    if coordinator_tree:
        for node in ast.walk(coordinator_tree):
            if isinstance(node, ast.Call) and hasattr(node.func, "id"):
                if node.func.id.startswith("create_") and node.func.id.endswith(
                    "_agent"
                ):
                    created_agents.add(node.func.id)

    # Check sub_agents list
    if coordinator_tree:
        for node in ast.walk(coordinator_tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "root_agent":
                        for kw in (
                            node.value.keywords
                            if isinstance(node.value, ast.Call)
                            else []
                        ):
                            if kw.arg == "sub_agents" and isinstance(
                                kw.value, ast.List
                            ):
                                for elt in kw.value.elts:
                                    if isinstance(elt, ast.Name):
                                        registered_agents.add(elt.id)

    # Check each agent file has a corresponding factory and registration
    for agent_file in agent_files:
        expected_factory = f"create_{agent_file}_agent"
        if expected_factory not in created_agents:
            findings.append(
                Finding(
                    field="agent_registration",
                    severity="error",
                    message=f"Agent factory '{expected_factory}' not found in app/agent.py",
                    file=str(coordinator_path),
                )
            )
        # Check the factory variable is in sub_agents list
        var_name = agent_file.replace("-", "_")
        if var_name not in registered_agents:
            findings.append(
                Finding(
                    field="agent_registration",
                    severity="error",
                    message=f"Agent '{var_name}' not found in root_agent sub_agents list",
                    file=str(coordinator_path),
                )
            )

    # Check all agents match file names
    for created in created_agents:
        expected_file = created.replace("create_", "").replace("_agent", "")
        if expected_file not in agent_files:
            findings.append(
                Finding(
                    field="agent_registration",
                    severity="warning",
                    message=f"Factory '{created}' has no corresponding file in app/agents/",
                    file=str(coordinator_path),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# 2. Tool registration
# ---------------------------------------------------------------------------


def check_tool_registration() -> list[Finding]:
    findings: list[Finding] = []

    tool_files = {_strip_init(p) for p in _py_files(TOOLS_DIR)}
    tool_files.discard("")

    referenced_tools: set[str] = set()
    for agent_file in _py_files(AGENTS_DIR):
        tree = _parse_ast(agent_file)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id.startswith("create_")
                        and "_agent" in target.id
                    ):
                        if isinstance(node.value, ast.Call):
                            for kw in (
                                node.value.keywords
                                if isinstance(node.value, ast.Call)
                                else []
                            ):
                                if kw.arg == "tools" and isinstance(kw.value, ast.List):
                                    for elt in kw.value.elts:
                                        if isinstance(elt, ast.Name):
                                            referenced_tools.add(elt.id)
                                        elif isinstance(elt, ast.Attribute):
                                            referenced_tools.add(elt.attr)

    # Check each referenced tool exists in app/tools/
    for tool_name in referenced_tools:
        likely_file = tool_name.replace("_", "_")
        if likely_file not in tool_files:
            findings.append(
                Finding(
                    field="tool_registration",
                    severity="error",
                    message=f"Tool '{tool_name}' referenced but no module found in app/tools/",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# 3. Missing tests
# ---------------------------------------------------------------------------


def check_missing_tests() -> list[Finding]:
    findings: list[Finding] = []

    for module_dir, _ in [
        (TOOLS_DIR, "tools"),
        (AGENTS_DIR, "agents"),
        (DATA_DIR, "data"),
        (MODELS_DIR, "models"),
    ]:
        for py_file in _py_files(module_dir):
            stem = _strip_init(py_file)
            if not stem:
                continue
            expected_test = UNIT_DIR / f"test_{stem}.py"
            if not expected_test.is_file():
                findings.append(
                    Finding(
                        field="missing_tests",
                        severity="warning",
                        message=f"No unit test for {stem}.py — expected at tests/unit/test_{stem}.py",
                        file=str(py_file),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 4. Circular imports
# ---------------------------------------------------------------------------


def _resolve_import_module(node: ast.AST, current_file: str) -> str | None:
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.startswith("app"):
                return alias.name
    elif isinstance(node, ast.ImportFrom):
        if node.module and node.module.startswith("app"):
            return node.module
    return None


def check_circular_imports() -> list[Finding]:
    findings: list[Finding] = []
    graph: dict[str, set[str]] = defaultdict(set)

    all_py_files = (
        list(_py_files(APP_DIR))
        + list(_py_files(AGENTS_DIR))
        + list(_py_files(TOOLS_DIR))
        + list(_py_files(MODELS_DIR))
        + list(_py_files(DATA_DIR))
        + list(_py_files(UTILS_DIR))
    )

    for py_file in all_py_files:
        rel = (
            os.path.relpath(py_file, APP_DIR.parent)
            .replace("\\", "/")
            .replace(".py", "")
            .replace("/", ".")
        )
        tree = _parse_ast(py_file)
        if not tree:
            continue
        for node in ast.walk(tree):
            mod = _resolve_import_module(node, str(py_file))
            if mod and mod != rel:
                graph[rel].add(mod)

    # DFS cycle detection using explicit state dict
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = dict.fromkeys(graph, WHITE)

    def _dfs_cycle(
        g: dict[str, set[str]],
        col: dict[str, int],
        node: str,
        path: list[str],
        out: list[Finding],
    ) -> None:
        col[node] = GRAY
        for neighbor in g.get(node, set()):
            if neighbor not in col:
                col[neighbor] = WHITE
            if col[neighbor] == GRAY:
                cycle = [*path[path.index(neighbor) :], neighbor]
                out.append(
                    Finding(
                        field="circular_imports",
                        severity="error",
                        message=f"Circular import detected: {' → '.join(cycle)}",
                    )
                )
            elif col[neighbor] == WHITE:
                _dfs_cycle(g, col, neighbor, [*path, neighbor], out)
        col[node] = BLACK

    for node in list(graph):
        if color.get(node, WHITE) == WHITE:
            _dfs_cycle(graph, color, node, [node], findings)

    return findings


# ---------------------------------------------------------------------------
# 5. Hardcoded models
# ---------------------------------------------------------------------------


def check_hardcoded_models() -> list[Finding]:
    findings: list[Finding] = []

    for py_file in _py_files(APP_DIR) + _py_files(AGENTS_DIR):
        src = _read_file(py_file)
        if 'Gemini(model="' in src or "Gemini(model='" in src:
            findings.append(
                Finding(
                    field="hardcoded_models",
                    severity="warning",
                    message="Hardcoded model name in Gemini() — consider using an environment variable",
                    file=str(py_file),
                )
            )
        # Check for any non-gemini-flash-latest model
        tree = _parse_ast(py_file)
        if tree:
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and hasattr(node.func, "attr")
                    and node.func.attr == "Gemini"
                ):
                    for kw in node.keywords:
                        if kw.arg == "model" and isinstance(kw.value, ast.Constant):
                            if kw.value.value != "gemini-flash-latest":
                                findings.append(
                                    Finding(
                                        field="hardcoded_models",
                                        severity="error",
                                        message=f"Unexpected model '{kw.value.value}' — only 'gemini-flash-latest' is allowed",
                                        file=str(py_file),
                                        line=node.lineno,
                                    )
                                )

    return findings


# ---------------------------------------------------------------------------
# 6. Hardcoded API keys
# ---------------------------------------------------------------------------


def check_hardcoded_api_keys() -> list[Finding]:
    findings: list[Finding] = []

    for py_file in _py_files(APP_DIR) + _py_files(AGENTS_DIR) + _py_files(TOOLS_DIR):
        src = _read_file(py_file)
        if "api_key=" in src or "api_key =" in src:
            findings.append(
                Finding(
                    field="hardcoded_api_keys",
                    severity="error",
                    message="api_key parameter detected — API keys must come from environment variables",
                    file=str(py_file),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# 7. Pydantic usage
# ---------------------------------------------------------------------------


def check_pydantic_usage() -> list[Finding]:
    findings: list[Finding] = []

    for py_file in _py_files(MODELS_DIR):
        src = _read_file(py_file)
        if "BaseModel" not in src:
            findings.append(
                Finding(
                    field="pydantic_usage",
                    severity="warning",
                    message=f"Model file {py_file.name} does not use BaseModel",
                    file=str(py_file),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# 8. Folder structure
# ---------------------------------------------------------------------------


def check_folder_structure() -> list[Finding]:
    findings: list[Finding] = []

    for req_dir in REQUIRED_DIRS:
        if not req_dir.is_dir():
            findings.append(
                Finding(
                    field="folder_structure",
                    severity="error",
                    message=f"Required directory missing: {req_dir.relative_to(PROJECT_ROOT)}",
                )
            )

    # Check that .agents subdirectories exist
    agents_subdirs = ["rules", "skills", "templates", "architecture"]
    for sub in agents_subdirs:
        path = PROJECT_ROOT / ".agents" / sub
        if not path.is_dir():
            findings.append(
                Finding(
                    field="folder_structure",
                    severity="warning",
                    message=f"Recommended directory missing: .agents/{sub}",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# 9. Naming conventions
# ---------------------------------------------------------------------------


def check_naming_conventions() -> list[Finding]:
    findings: list[Finding] = []

    for root_dir in [APP_DIR, TESTS_DIR]:
        if not root_dir.is_dir():
            continue
        for py_file in root_dir.rglob("*.py"):
            rel = py_file.relative_to(PROJECT_ROOT)
            name = py_file.stem
            if name == "__init__":
                continue
            if name != name.lower():
                findings.append(
                    Finding(
                        field="naming_conventions",
                        severity="error",
                        message=f"File name must be lowercase snake_case: {rel}",
                        file=str(rel),
                    )
                )
            if "_" in name and any(c.isupper() for c in name):
                findings.append(
                    Finding(
                        field="naming_conventions",
                        severity="error",
                        message=f"File name contains uppercase chars: {rel}",
                        file=str(rel),
                    )
                )

    # Check test file naming
    for test_file in _py_files(UNIT_DIR):
        name = test_file.stem
        if not name.startswith("test_"):
            findings.append(
                Finding(
                    field="naming_conventions",
                    severity="error",
                    message=f"Test file must start with 'test_': tests/unit/{test_file.name}",
                    file=str(test_file),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# 10. Forbidden imports
# ---------------------------------------------------------------------------


def check_forbidden_imports() -> list[Finding]:
    findings: list[Finding] = []

    all_py = (
        list(_py_files(APP_DIR))
        + list(_py_files(AGENTS_DIR))
        + list(_py_files(TOOLS_DIR))
    )
    for py_file in all_py:
        tree = _parse_ast(py_file)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        full = f"{node.module}.{alias.name}"
                        if full in FORBIDDEN_IMPORTS or alias.name in {
                            "Dict",
                            "List",
                            "Optional",
                            "Tuple",
                            "Set",
                            "Callable",
                            "Type",
                        }:
                            findings.append(
                                Finding(
                                    field="forbidden_imports",
                                    severity="error",
                                    message=f"Forbidden import '{full}' in {py_file.name} — use modern syntax (list, dict, str | None, etc.)",
                                    file=str(py_file),
                                    line=node.lineno,
                                )
                            )

    return findings


# ---------------------------------------------------------------------------
# 11. Dependency direction
# ---------------------------------------------------------------------------


def check_dependency_direction() -> list[Finding]:
    findings: list[Finding] = []

    for module_dir, label in [
        (AGENTS_DIR, "app.agents"),
        (TOOLS_DIR, "app.tools"),
        (DATA_DIR, "app.data"),
        (MODELS_DIR, "app.models"),
        (UTILS_DIR, "app.app_utils"),
    ]:
        allowed = ALLOWED_DEPENDENCIES.get(label, set())
        for py_file in _py_files(module_dir):
            tree = _parse_ast(py_file)
            if not tree:
                continue
            for node in ast.walk(tree):
                imported = _resolve_import_module(node, str(py_file))
                if imported and imported.startswith("app"):
                    imported_base = ".".join(imported.split(".")[:2])
                    if imported_base != label and imported_base not in allowed:
                        findings.append(
                            Finding(
                                field="dependency_direction",
                                severity="error",
                                message=f"{label} imports {imported_base} (not allowed) in {py_file.name}",
                                file=str(py_file),
                                line=getattr(node, "lineno", 0),
                            )
                        )

    return findings


# ---------------------------------------------------------------------------
# 12. Unreferenced files
# ---------------------------------------------------------------------------


def check_unreferenced_files() -> list[Finding]:
    findings: list[Finding] = []
    all_imports: set[str] = set()
    all_modules: set[str] = set()

    for py_file in (
        list(_py_files(APP_DIR))
        + list(_py_files(AGENTS_DIR))
        + list(_py_files(TOOLS_DIR))
    ):
        rel = (
            os.path.relpath(py_file, PROJECT_ROOT)
            .replace("\\", "/")
            .replace(".py", "")
            .replace("/", ".")
        )
        if py_file.stem != "__init__":
            all_modules.add(rel)

        tree = _parse_ast(py_file)
        if not tree:
            continue
        for node in ast.walk(tree):
            mod = _resolve_import_module(node, str(py_file))
            if mod:
                all_imports.add(mod)

    for mod in sorted(all_modules):
        if mod not in all_imports and mod != "app.__init__":
            findings.append(
                Finding(
                    field="unreferenced_files",
                    severity="warning",
                    message=f"Module '{mod}' is not imported anywhere in the project",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


CHECKS: list[tuple[str, Any]] = [
    ("Agent registration", check_agent_registration),
    ("Tool registration", check_tool_registration),
    ("Missing tests", check_missing_tests),
    ("Circular imports", check_circular_imports),
    ("Hardcoded models", check_hardcoded_models),
    ("Hardcoded API keys", check_hardcoded_api_keys),
    ("Pydantic usage", check_pydantic_usage),
    ("Folder structure", check_folder_structure),
    ("Naming conventions", check_naming_conventions),
    ("Forbidden imports", check_forbidden_imports),
    ("Dependency direction", check_dependency_direction),
    ("Unreferenced files", check_unreferenced_files),
]


def main() -> int:
    all_findings: list[Finding] = []
    errors = 0
    warnings = 0

    for name, check_fn in CHECKS:
        try:
            findings = check_fn()
        except Exception as e:
            findings = [
                Finding(
                    field=name.lower().replace(" ", "_"),
                    severity="error",
                    message=f"Checker '{name}' raised an exception: {e}",
                )
            ]

        for f in findings:
            if f.severity == "error":
                errors += 1
            else:
                warnings += 1
        all_findings.extend(findings)

    # Sort: errors first, then by field
    all_findings.sort(
        key=lambda f: (0 if f.severity == "error" else 1, f.field, f.file)
    )

    print("=" * 70)
    print("  Project Validation Report")
    print("=" * 70)

    for f in all_findings:
        tag = "ERROR" if f.severity == "error" else "WARN"
        location = f"  [{f.file}:{f.line}]" if f.file else ""
        print(f"  {tag}  [{f.field}] {f.message}{location}")

    print("=" * 70)
    print(f"  {errors} error(s), {warnings} warning(s)")
    print("=" * 70)

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

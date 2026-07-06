"""
validate_agents.py — Agent integrity checks for meal-planner-assistant.

Validates:
  1. Single responsibility       5. Agent registration
  2. Allowed tool usage          6. Shared memory usage
  3. Prompt separation           7. Context management
  4. Prompt completeness

Exit code 0 = all pass, 1 = failures found.
"""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
AGENTS_DIR = APP_DIR / "agents"
TOOLS_DIR = APP_DIR / "tools"
COORDINATOR_PATH = APP_DIR / "agent.py"


@dataclass
class Finding:
    field: str
    severity: str
    message: str
    file: str = ""
    line: int = 0


REQUIRED_INSTRUCTION_SECTIONS = [
    "session state",
    "Reads",
    "Writes",
]

AGENT_RESPONSIBILITY_MAP: dict[str, list[str]] = {
    "profile": ["user_profile", "dietary", "allergy", "goal", "budget"],
    "inventory": ["available_ingredients", "requested_ingredients", "normalize"],
    "recipe": ["selected_recipes", "recommend", "rank", "diversity"],
    "meal_plan": ["meal_plan", "plan", "schedule"],
    "nutrition": ["nutrition_validation", "calorie", "macro", "protein"],
    "shopping": ["shopping_list", "cost", "estimate", "category"],
}


def _get_agent_files() -> list[Path]:
    if not AGENTS_DIR.exists():
        return []
    return sorted(p for p in AGENTS_DIR.glob("*.py") if p.stem != "__init__")


def _get_tool_functions() -> set[str]:
    funcs: set[str] = set()
    if not TOOLS_DIR.exists():
        return funcs
    for py_file in TOOLS_DIR.glob("*.py"):
        tree = _parse_ast(py_file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                funcs.add(node.name)
    return funcs


def _parse_ast(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return None


def _get_agent_name_from_factory(factory_name: str) -> str:
    return factory_name.replace("create_", "").replace("_agent", "")


# ---------------------------------------------------------------------------
# 1. Single responsibility
# ---------------------------------------------------------------------------


def check_single_responsibility() -> list[Finding]:
    findings: list[Finding] = []
    for agent_file in _get_agent_files():
        tree = _parse_ast(agent_file)
        if tree is None:
            continue

        name = agent_file.stem
        expected_keywords = AGENT_RESPONSIBILITY_MAP.get(name, [name])

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name.startswith("create_")
                and node.name.endswith("_agent")
            ):
                agent_name = _get_agent_name_from_factory(node.name)
                if agent_name != name:
                    continue

                instruction = _extract_instruction(node)
                if instruction is None:
                    findings.append(
                        Finding(
                            field="single_responsibility",
                            severity="error",
                            message=f"Agent factory '{node.name}' has no instruction string",
                            file=str(agent_file),
                            line=node.lineno,
                        )
                    )
                    continue

                instruction_lower = instruction.lower()
                matches = sum(1 for kw in expected_keywords if kw in instruction_lower)
                if matches == 0:
                    findings.append(
                        Finding(
                            field="single_responsibility",
                            severity="warning",
                            message=f"Agent '{agent_name}' instruction does not mention its expected domain: {expected_keywords}",
                            file=str(agent_file),
                            line=node.lineno,
                        )
                    )

    return findings


def _extract_instruction(node: ast.FunctionDef) -> str | None:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            for kw in child.keywords if hasattr(child, "keywords") else []:
                if kw.arg in ("instruction", "system_instruction"):
                    if isinstance(kw.value, ast.Constant) and isinstance(
                        kw.value.value, str
                    ):
                        return kw.value.value
                    if isinstance(kw.value, ast.JoinedStr):
                        parts: list[str] = []
                        for part in kw.value.values:
                            if isinstance(part, ast.Constant) and isinstance(
                                part.value, str
                            ):
                                parts.append(part.value)
                            elif isinstance(part, ast.FormattedValue):
                                parts.append("{...}")
                        return "".join(parts)
    return None


# ---------------------------------------------------------------------------
# 2. Allowed tool usage
# ---------------------------------------------------------------------------


def check_allowed_tool_usage() -> list[Finding]:
    findings: list[Finding] = []
    tool_functions = _get_tool_functions()

    for agent_file in _get_agent_files():
        tree = _parse_ast(agent_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords if hasattr(node, "keywords") else []:
                    if kw.arg == "tools" and isinstance(kw.value, ast.List):
                        for elt in kw.value.elts:
                            if (
                                isinstance(elt, ast.Name)
                                and elt.id not in tool_functions
                            ):
                                findings.append(
                                    Finding(
                                        field="allowed_tool_usage",
                                        severity="error",
                                        message=f"Tool '{elt.id}' referenced in agent '{agent_file.stem}' not found in app/tools/",
                                        file=str(agent_file),
                                        line=elt.lineno,
                                    )
                                )

    return findings


# ---------------------------------------------------------------------------
# 3. Prompt separation
# ---------------------------------------------------------------------------


def check_prompt_separation() -> list[Finding]:
    findings: list[Finding] = []
    for agent_file in _get_agent_files():
        tree = _parse_ast(agent_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name.startswith("create_")
                and node.name.endswith("_agent")
            ):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        for kw in child.keywords if hasattr(child, "keywords") else []:
                            if kw.arg in ("instruction", "system_instruction"):
                                if isinstance(kw.value, ast.Constant) and isinstance(
                                    kw.value.value, str
                                ):
                                    instr = kw.value.value
                                    if len(instr) < 50:
                                        findings.append(
                                            Finding(
                                                field="prompt_separation",
                                                severity="warning",
                                                message=f"Agent '{node.name}' instruction is very short ({len(instr)} chars) — may lack sufficient guidance",
                                                file=str(agent_file),
                                                line=kw.lineno,
                                            )
                                        )

    return findings


# ---------------------------------------------------------------------------
# 4. Prompt completeness
# ---------------------------------------------------------------------------


def check_prompt_completeness() -> list[Finding]:
    findings: list[Finding] = []
    for agent_file in _get_agent_files():
        tree = _parse_ast(agent_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name.startswith("create_")
                and node.name.endswith("_agent")
            ):
                instruction = _extract_instruction(node)
                if instruction is None:
                    continue
                instruction_lower = instruction.lower()
                for section in REQUIRED_INSTRUCTION_SECTIONS:
                    if section not in instruction_lower:
                        findings.append(
                            Finding(
                                field="prompt_completeness",
                                severity="warning",
                                message=f"Agent '{node.name}' instruction missing '{section}' section — should document session state keys",
                                file=str(agent_file),
                                line=node.lineno,
                            )
                        )

    return findings


# ---------------------------------------------------------------------------
# 5. Agent registration
# ---------------------------------------------------------------------------


def check_agent_registration() -> list[Finding]:
    findings: list[Finding] = []
    agent_files = {f.stem for f in _get_agent_files()}

    if not COORDINATOR_PATH.exists():
        findings.append(
            Finding(
                field="agent_registration",
                severity="error",
                message=f"Coordinator file not found at {COORDINATOR_PATH}",
            )
        )
        return findings

    coordinator_text = COORDINATOR_PATH.read_text(encoding="utf-8")

    for agent_file in agent_files:
        expected_factory = f"create_{agent_file}_agent"
        if expected_factory not in coordinator_text:
            findings.append(
                Finding(
                    field="agent_registration",
                    severity="error",
                    message=f"Agent factory '{expected_factory}' not referenced in {COORDINATOR_PATH.name}",
                    file=str(COORDINATOR_PATH),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# 6. Shared memory usage
# ---------------------------------------------------------------------------


def check_shared_memory_usage() -> list[Finding]:
    findings: list[Finding] = []
    for agent_file in _get_agent_files():
        tree = _parse_ast(agent_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name.startswith("create_")
                and node.name.endswith("_agent")
            ):
                instruction = _extract_instruction(node)
                if instruction is None:
                    continue

                session_state_refs = [
                    line
                    for line in instruction.split("\n")
                    if "session_state" in line.lower() or "session" in line.lower()
                ]
                if len(session_state_refs) == 0:
                    findings.append(
                        Finding(
                            field="shared_memory_usage",
                            severity="warning",
                            message=f"Agent '{node.name}' instruction does not reference session state — agents should document state keys",
                            file=str(agent_file),
                            line=node.lineno,
                        )
                    )

    return findings


# ---------------------------------------------------------------------------
# 7. Context management
# ---------------------------------------------------------------------------


def check_context_management() -> list[Finding]:
    findings: list[Finding] = []
    for agent_file in _get_agent_files():
        tree = _parse_ast(agent_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name.startswith("create_")
                and node.name.endswith("_agent")
            ):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        for kw in child.keywords if hasattr(child, "keywords") else []:
                            if (
                                kw.arg == "context"
                                or kw.arg == "before_model_callback"
                                or kw.arg == "after_model_callback"
                            ):
                                findings.append(
                                    Finding(
                                        field="context_management",
                                        severity="info",
                                        message=f"Agent '{node.name}' uses '{kw.arg}' — verify context management is appropriate",
                                        file=str(agent_file),
                                        line=kw.lineno,
                                    )
                                )

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CHECKS: list[tuple[str, str, Any]] = [
    ("Single responsibility", "error", check_single_responsibility),
    ("Allowed tool usage", "error", check_allowed_tool_usage),
    ("Prompt separation", "warning", check_prompt_separation),
    ("Prompt completeness", "warning", check_prompt_completeness),
    ("Agent registration", "error", check_agent_registration),
    ("Shared memory usage", "warning", check_shared_memory_usage),
    ("Context management", "info", check_context_management),
]


def main() -> int:
    all_findings: list[Finding] = []
    for check_name, _severity, check_func in CHECKS:
        try:
            findings = check_func()
            if findings:
                for f in findings:
                    tag = (
                        "FAIL"
                        if f.severity == "error"
                        else "WARN"
                        if f.severity == "warning"
                        else "INFO"
                    )
                    loc = f" [{f.file}" + (f":{f.line}" if f.line else "") + "]"
                    print(f"  [{tag}] {f.field}: {f.message}{loc}")
                all_findings.extend(findings)
        except Exception as e:
            print(f"  [ERROR] {check_name} crashed: {e}", file=sys.stderr)
            all_findings.append(
                Finding(
                    field=check_name, severity="error", message=f"Checker crashed: {e}"
                )
            )

    errors = [f for f in all_findings if f.severity == "error"]
    warnings = [f for f in all_findings if f.severity == "warning"]

    print(
        f"\nAgent validation: {len(errors)} errors, {len(warnings)} warnings, {len(all_findings)} total"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

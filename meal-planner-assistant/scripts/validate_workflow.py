"""
validate_workflow.py — Workflow graph integrity checks for meal-planner-assistant.

Validates:
  1. Orphan nodes                      5. Human-in-the-Loop placement
  2. Invalid graph edges               6. Deterministic nodes before LLM nodes
  3. Cycles where not allowed          7. Retry nodes on LLM edges
  4. Security Checkpoint placement     8. Workflow metadata

Exit code 0 = all pass, 1 = failures found.
"""

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
AGENTS_DIR = APP_DIR / "agents"
ARCHITECTURE_DIR = PROJECT_ROOT / ".agents" / "architecture"


@dataclass
class Finding:
    field: str
    severity: str
    message: str
    file: str = ""
    line: int = 0


LLM_NODE_PATTERNS = [
    "recipe_ranking",
    "recipe_recommendation",
    "portion_adjustment",
    "preference_extraction",
    "ingredient_substitution",
    "diversity_evaluation",
    "friendly_summary",
]

DETERMINISTIC_NODE_PATTERNS = [
    "validate_",
    "normalize_",
    "calculate_",
    "generate_optimized_",
    "estimate_",
    "security_checkpoint",
    "input_validation",
    "allergy_filter",
    "availability_scoring",
    "cost_estimation",
    "budget_check",
    "dedup",
    "merge",
    "rotation",
    "nutrition_analysis",
    "profile_collection",
    "inventory_normalization",
]


# ---------------------------------------------------------------------------
# 1. Orphan nodes
# ---------------------------------------------------------------------------


def _extract_nodes_from_mermaid(text: str) -> dict[str, str]:
    """Extract node definitions from Mermaid flowchart TD syntax.
    Returns {node_id: node_label}.
    """
    nodes: dict[str, str] = {}

    # Match node definitions like: SC[Security Checkpoint]
    # or: NODE_ID([Label])
    patterns = [
        r"(\w+)\[([^\]]+)\]",  # SC[Security Checkpoint]
        r"(\w+)\(\(([^)]+)\)\)",  # START((User Request))
        r"(\w+)\{([^}]+)\}",  # HU1{Human: Confirm}
        r"(\w+)\(([^)]+)\)",  # DET1(Deterministic)
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            nodes[m.group(1)] = m.group(2).strip()

    return nodes


def _extract_edges_from_mermaid(text: str) -> list[tuple[str, str]]:
    """Extract directed edges from Mermaid syntax.
    Returns [(source, target), ...].
    """
    edges: list[tuple[str, str]] = []
    # Match: NODE1 --> NODE2 or NODE1 -->|Label| NODE2
    pattern = r"(\w+)\s*-->(\|([^|]*)\|)?\s*(\w+)"
    for m in re.finditer(pattern, text):
        edges.append((m.group(1), m.group(4)))
    return edges


def check_orphan_nodes(arch_files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for arch_file in arch_files:
        text = arch_file.read_text(encoding="utf-8")
        nodes = _extract_nodes_from_mermaid(text)
        edges = _extract_edges_from_mermaid(text)

        connected: set[str] = set()
        for src, tgt in edges:
            connected.add(src)
            connected.add(tgt)

        for node_id, label in nodes.items():
            if node_id not in connected and not node_id.startswith("START"):
                findings.append(
                    Finding(
                        field="orphan_nodes",
                        severity="warning",
                        message=f"Orphan node '{node_id}' ({label}) in {arch_file.name} — not connected to any edge",
                        file=str(arch_file),
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# 2. Invalid graph edges
# ---------------------------------------------------------------------------


def check_invalid_edges(arch_files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for arch_file in arch_files:
        text = arch_file.read_text(encoding="utf-8")
        nodes = _extract_nodes_from_mermaid(text)
        edges = _extract_edges_from_mermaid(text)

        for src, tgt in edges:
            if src not in nodes:
                findings.append(
                    Finding(
                        field="invalid_edges",
                        severity="error",
                        message=f"Edge source '{src}' not defined as a node in {arch_file.name}",
                        file=str(arch_file),
                    )
                )
            if tgt not in nodes:
                findings.append(
                    Finding(
                        field="invalid_edges",
                        severity="error",
                        message=f"Edge target '{tgt}' not defined as a node in {arch_file.name}",
                        file=str(arch_file),
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# 3. Cycles where not allowed
# ---------------------------------------------------------------------------


def _dfs_check_cycles(
    graph: dict[str, list[str]],
    arch_file_name: str,
    findings: list[Finding],
) -> None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {}

    def _dfs(node: str, path: list[str]) -> None:
        color[node] = GRAY
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                color[neighbor] = WHITE
            if color[neighbor] == GRAY:
                cycle_path = [*path[path.index(neighbor) :], neighbor]
                is_allowed = any(
                    "validation" in n.lower()
                    or "retry" in n.lower()
                    or "reject" in n.lower()
                    for n in cycle_path
                )
                if not is_allowed:
                    findings.append(
                        Finding(
                            field="cycles",
                            severity="error",
                            message=f"Unexpected cycle detected: {' → '.join(cycle_path)}",
                            file=arch_file_name,
                        )
                    )
            elif color[neighbor] == WHITE:
                _dfs(neighbor, [*path, neighbor])
        color[node] = BLACK

    for node in list(graph):
        if node not in color:
            _dfs(node, [node])


def check_cycles(arch_files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for arch_file in arch_files:
        text = arch_file.read_text(encoding="utf-8")
        edges = _extract_edges_from_mermaid(text)

        graph: dict[str, list[str]] = {}
        for src, tgt in edges:
            graph.setdefault(src, []).append(tgt)

        _dfs_check_cycles(graph, str(arch_file), findings)

    return findings


# ---------------------------------------------------------------------------
# 4. Security Checkpoint placement
# ---------------------------------------------------------------------------


def check_security_checkpoint_placement(arch_files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for arch_file in arch_files:
        text = arch_file.read_text(encoding="utf-8")
        nodes = _extract_nodes_from_mermaid(text)
        edges = _extract_edges_from_mermaid(text)

        graph: dict[str, list[str]] = {}
        for src, tgt in edges:
            graph.setdefault(src, []).append(tgt)

        llm_nodes = {
            nid
            for nid, lbl in nodes.items()
            if any(
                p in lbl.lower()
                for p in [
                    "llm:",
                    "recipe ranking",
                    "portion adjustment",
                    "preference extraction",
                    "diversity",
                    "substitution",
                ]
            )
        }

        for llm_node in llm_nodes:
            has_security_gate = False
            for src, tgts in graph.items():
                if llm_node in tgts and "sc" in src.lower():
                    has_security_gate = True
                    break
            if not has_security_gate:
                findings.append(
                    Finding(
                        field="security_checkpoint_placement",
                        severity="error",
                        message=f"LLM node '{llm_node}' ({nodes.get(llm_node, '')}) lacks a preceding Security Checkpoint node",
                        file=str(arch_file),
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# 5. Human-in-the-Loop placement
# ---------------------------------------------------------------------------


def check_human_in_the_loop(arch_files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for arch_file in arch_files:
        text = arch_file.read_text(encoding="utf-8")
        nodes = _extract_nodes_from_mermaid(text)
        edges = _extract_edges_from_mermaid(text)

        graph: dict[str, list[str]] = {}
        for src, tgt in edges:
            graph.setdefault(src, []).append(tgt)

        hitl_nodes = {
            nid
            for nid, lbl in nodes.items()
            if any(p in lbl.lower() for p in ["human", "confirm", "accept", "reject"])
        }

        for hitl_node in hitl_nodes:
            predecessors = [src for src, tgts in graph.items() if hitl_node in tgts]
            has_deterministic_predecessor = False
            for pred in predecessors:
                label = nodes.get(pred, "").lower()
                if any(
                    p in label
                    for p in [
                        "deterministic",
                        "validate",
                        "calculate",
                        "generate",
                        "output",
                    ]
                ):
                    has_deterministic_predecessor = True
                    break
            if not has_deterministic_predecessor and predecessors:
                findings.append(
                    Finding(
                        field="human_in_the_loop_placement",
                        severity="warning",
                        message=f"HITL node '{hitl_node}' ({nodes.get(hitl_node, '')}) should follow a deterministic output node",
                        file=str(arch_file),
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# 6. Deterministic nodes before LLM nodes
# ---------------------------------------------------------------------------


def check_deterministic_before_llm(arch_files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for arch_file in arch_files:
        text = arch_file.read_text(encoding="utf-8")
        nodes = _extract_nodes_from_mermaid(text)
        edges = _extract_edges_from_mermaid(text)

        graph: dict[str, list[str]] = {}
        for src, tgt in edges:
            graph.setdefault(src, []).append(tgt)

        llm_nodes = {
            nid
            for nid, lbl in nodes.items()
            if any(
                p in lbl.lower()
                for p in ["llm:", "recipe ranking", "portion adjustment"]
            )
        }

        for llm_node in llm_nodes:
            predecessors = [src for src, tgts in graph.items() if llm_node in tgts]
            has_deterministic = False
            for pred in predecessors:
                label = nodes.get(pred, "").lower()
                if (
                    any(p in label for p in DETERMINISTIC_NODE_PATTERNS)
                    or "deterministic" in label
                ):
                    has_deterministic = True
                    break
            if not has_deterministic and len(predecessors) > 0:
                findings.append(
                    Finding(
                        field="deterministic_before_llm",
                        severity="error",
                        message=f"LLM node '{llm_node}' ({nodes.get(llm_node, '')}) has no deterministic predecessor — business rules must execute before LLM",
                        file=str(arch_file),
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# 7. Retry nodes on LLM edges
# ---------------------------------------------------------------------------


def check_retry_configuration(arch_files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for arch_file in arch_files:
        text = arch_file.read_text(encoding="utf-8")
        nodes = _extract_nodes_from_mermaid(text)
        edges = _extract_edges_from_mermaid(text)

        graph: dict[str, list[str]] = {}
        for src, tgt in edges:
            graph.setdefault(src, []).append(tgt)

        llm_nodes = {
            nid
            for nid, lbl in nodes.items()
            if any(p in lbl.lower() for p in ["llm:", "recipe ranking"])
        }

        for llm_node in llm_nodes:
            successors = graph.get(llm_node, [])
            has_retry = False
            for succ in successors:
                label = nodes.get(succ, "").lower()
                if "retry" in label or "fail" in label:
                    has_retry = True
                    break
            if not has_retry:
                findings.append(
                    Finding(
                        field="retry_configuration",
                        severity="warning",
                        message=f"LLM node '{llm_node}' ({nodes.get(llm_node, '')}) lacks a retry/fallback edge",
                        file=str(arch_file),
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# 8. Workflow metadata
# ---------------------------------------------------------------------------

WORKFLOW_REQUIRED_FIELDS = [
    "Purpose",
    "Trigger",
    "Inputs",
    "Outputs",
    "Nodes",
    "Edges",
    "Validation Checkpoints",
    "Human Approval",
    "Failure Handling",
    "Retry Strategy",
    "LLM steps",
    "No-LLM steps",
]


def check_workflow_metadata(arch_files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for arch_file in arch_files:
        text = arch_file.read_text(encoding="utf-8")
        # Find workflow sections (headers like "### N. Title")
        workflow_sections = re.findall(r"### \d+\.\s*(.+?)\n", text)

        for section_title in workflow_sections:
            for required_field in WORKFLOW_REQUIRED_FIELDS:
                # Check if the field header exists within this section
                field_pattern = r"\|?\s*" + re.escape(required_field) + r"\s*\|?"
                if not re.search(field_pattern, text, re.IGNORECASE):
                    # Check the section block following the title
                    section_match = re.search(
                        re.escape(section_title) + r".*?(?=### |\Z)", text, re.DOTALL
                    )
                    if section_match and required_field not in section_match.group():
                        findings.append(
                            Finding(
                                field="workflow_metadata",
                                severity="warning",
                                message=f"Workflow '{section_title}' missing required field: '{required_field}'",
                                file=str(arch_file),
                            )
                        )

    return findings


# ---------------------------------------------------------------------------
# Check coordinator prompt in app/agent.py
# ---------------------------------------------------------------------------


def check_coordinator_workflow() -> list[Finding]:
    findings: list[Finding] = []
    agent_py = APP_DIR / "agent.py"
    if not agent_py.is_file():
        return findings

    src = agent_py.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(agent_py))

    # Extract sub_agents list
    sub_agents: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "root_agent":
                    if isinstance(node.value, ast.Call):
                        for kw in node.value.keywords:
                            if kw.arg == "sub_agents" and isinstance(
                                kw.value, ast.List
                            ):
                                for elt in kw.value.elts:
                                    if isinstance(elt, ast.Name):
                                        sub_agents.append(elt.id)

    # Check that coordinator instruction mentions all sub-agent tasks
    if sub_agents:
        for var_name in sub_agents:
            agent_name = var_name.replace("_agent", "")
            # Check instruction mentions the agent's domain
            if agent_name not in src.lower():
                findings.append(
                    Finding(
                        field="coordinator_workflow",
                        severity="warning",
                        message=f"Coordinator instruction may not reference '{agent_name}' agent workflow",
                        file=str(agent_py),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


CHECKS: list[tuple[str, Any]] = [
    ("Orphan nodes", lambda: check_orphan_nodes(arch_files)),
    ("Invalid graph edges", lambda: check_invalid_edges(arch_files)),
    ("Unexpected cycles", lambda: check_cycles(arch_files)),
    (
        "Security Checkpoint placement",
        lambda: check_security_checkpoint_placement(arch_files),
    ),
    ("Human-in-the-Loop placement", lambda: check_human_in_the_loop(arch_files)),
    ("Deterministic before LLM", lambda: check_deterministic_before_llm(arch_files)),
    ("Retry configuration", lambda: check_retry_configuration(arch_files)),
    ("Workflow metadata", lambda: check_workflow_metadata(arch_files)),
    ("Coordinator workflow completeness", check_coordinator_workflow),
]


def main() -> int:
    global arch_files
    arch_files = (
        list(ARCHITECTURE_DIR.glob("*.md")) if ARCHITECTURE_DIR.is_dir() else []
    )

    if not arch_files:
        print(
            "  WARN  [workflow_metadata] No architecture documents found in .agents/architecture/"
        )
        print("=" * 70)
        print("  Project Validation Report")
        print("=" * 70)
        print("  0 error(s), 0 warning(s)")
        print("=" * 70)
        return 0

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

    all_findings.sort(
        key=lambda f: (0 if f.severity == "error" else 1, f.field, f.file)
    )

    print("=" * 70)
    print("  Workflow Validation Report")
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

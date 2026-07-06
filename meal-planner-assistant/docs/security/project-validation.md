# Project Validation Reference

This document catalogs all project validator scripts and their checks.

## Validator Scripts

| Script | Stages | Checks | Entry Point |
|--------|--------|--------|-------------|
| `validate_project.py` | 5 | 12 structural checks | `uv run python scripts/validate_project.py` |
| `validate_workflow.py` | 6 | 9 workflow graph checks | `uv run python scripts/validate_workflow.py` |
| `validate_agents.py` | 7 | 7 agent integrity checks | `uv run python scripts/validate_agents.py` |
| `validate_domain.py` | 8 | 12 domain model checks | `uv run python scripts/validate_domain.py` |
| `validate_prompts.py` | 9 | 6 prompt integrity checks | `uv run python scripts/validate_prompts.py` |
| `validate_mcp.py` | 10 | 8 MCP configuration checks | `uv run python scripts/validate_mcp.py` |

All scripts follow the same pattern:
- Return `0` if all checks pass
- Return `1` if any ERROR-severity check fails
- Print findings to stdout with tags: `[FAIL]`, `[WARN]`, `[INFO]`

---

## 1. validate_project.py

**File:** `scripts/validate_project.py`

**12 checks:**

| # | Check | Severity | What It Validates |
|---|-------|----------|-------------------|
| 1 | Agent registration | ERROR | All agent factories in `app/agents/` are imported and registered in `app/agent.py`'s `sub_agents` list |
| 2 | Tool registration | ERROR | All tools referenced in agent `tools=[]` lists have a corresponding function in `app/tools/` |
| 3 | Missing tests | WARNING | Each `.py` file in `app/` has a corresponding test file in `tests/unit/` |
| 4 | Circular imports | ERROR | No cycles in the `app/` import graph (DFS-based detection) |
| 5 | Hardcoded models | ERROR/WARN | Only `gemini-flash-latest` model string allowed; all others flagged |
| 6 | Hardcoded API keys | ERROR | No `api_key=` parameter in any `.py` file |
| 7 | Pydantic usage | WARNING | Models in `app/models/` use `BaseModel` for schema definition |
| 8 | Folder structure | ERROR | Required directories (`app/`, `tests/`, `scripts/`, etc.) exist |
| 9 | Naming conventions | ERROR | `snake_case` for files, `test_` prefix for test files, `create_*_agent` for agent factories |
| 10 | Forbidden imports | ERROR | No `Dict`, `List`, `Optional`, `Tuple` from `typing` — use builtins |
| 11 | Dependency direction | ERROR | Dependency flows: Agents → Tools → Data → Models only; no reverse dependencies |
| 12 | Unreferenced files | WARNING | Files in `app/` not imported anywhere |

**How to add a check:**
```python
def check_my_new_rule() -> list[Finding]:
    findings: list[Finding] = []
    # ... validation logic ...
    return findings

# Then add to CHECKS list
CHECKS: list[tuple[str, str, Any]] = [
    ...
    ("My new rule", "error", check_my_new_rule),
]
```

---

## 2. validate_workflow.py

**File:** `scripts/validate_workflow.py`

**9 checks:**

| # | Check | Severity | What It Validates |
|---|-------|----------|-------------------|
| 1 | Orphan nodes | WARNING | All nodes in the Mermaid graph are connected to at least one edge |
| 2 | Invalid graph edges | ERROR | Edge sources and targets reference only defined nodes |
| 3 | Unexpected cycles | ERROR | Cycles only permitted for validation/retry/rejection loops |
| 4 | Security Checkpoint placement | ERROR | Every LLM node has a preceding `Security Checkpoint` node |
| 5 | Human-in-the-Loop placement | WARNING | HITL nodes follow a deterministic output predecessor |
| 6 | Deterministic before LLM | ERROR | Business rule nodes (validate, calculate, normalize) execute before any LLM node |
| 7 | Retry configuration | WARNING | LLM nodes have a retry/fallback outgoing edge |
| 8 | Workflow metadata | WARNING | `.agents/architecture/*.md` contains all required metadata sections |
| 9 | Coordinator completeness | WARNING | Coordinator instruction references all sub-agent tasks |

**How it works:**
- Parses Mermaid `flowchart TD` diagrams from `.agents/architecture/*.md`
- Extracts node IDs/labels and edge definitions via regex
- Builds a directed graph and runs graph algorithms (DFS for cycles, BFS for connectivity)

**How to add a check:**
```python
def check_my_new_rule(arch_files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    # ... validation logic ...
    return findings

# Then add to CHECKS list
CHECKS: list[tuple[str, str, Any]] = [
    ...
    ("My new rule", "error", check_my_new_rule),
]
```

---

## 3. validate_agents.py

**File:** `scripts/validate_agents.py`

**7 checks:**

| # | Check | Severity | What It Validates |
|---|-------|----------|-------------------|
| 1 | Single responsibility | ERROR/WARN | Agent instruction mentions its expected domain keywords |
| 2 | Allowed tool usage | ERROR | Tools referenced in `tools=[]` exist in `app/tools/` |
| 3 | Prompt separation | WARNING | Instructions are sufficiently long and descriptive |
| 4 | Prompt completeness | WARNING | Instructions document session state keys (Reads/Writes) |
| 5 | Agent registration | ERROR | All agent factories are referenced in the coordinator |
| 6 | Shared memory usage | WARNING | Instructions reference session state |
| 7 | Context management | INFO | Detects use of callback/context parameters |

---

## 4. validate_domain.py

**File:** `scripts/validate_domain.py`

**12 checks:**

### Meal Plan Checks
| # | Check | Severity | What It Validates |
|---|-------|----------|-------------------|
| 1 | Calorie limits | WARNING | Recipes within 800–3500 cal range |
| 2 | Macro limits | WARNING | Protein ≤ 250g, carbs ≤ 500g, fat ≤ 150g |
| 3 | Allergy safety | WARNING | Allergen tags use known allergen names |
| 4 | Dietary restrictions | WARNING | Dietary tags are from the valid set |
| 5 | Duplicate meals | ERROR | No duplicate recipe names |
| 6 | Meal diversity | INFO | At least 2 dietary tags across 3+ recipes |

### Shopping List Checks
| # | Check | Severity | What It Validates |
|---|-------|----------|-------------------|
| 7 | Duplicate ingredients | ERROR | No duplicate keys in PRICE_DB |
| 8 | Ingredient reuse | INFO | Ingredients appear across multiple recipes |
| 9 | Owned ingredient removal | WARNING | Inventory agent filters available ingredients |
| 10 | Cost estimation | WARNING | Cost estimator references PRICE_DB |

### Recipe Checks
| # | Check | Severity | What It Validates |
|---|-------|----------|-------------------|
| 11 | Normalized ingredients | WARNING | normalize_ingredient_name works on recipe ingredients |
| 12 | Valid identifiers | ERROR/WARN | Recipe IDs and ingredient keys use valid format |

---

## 5. validate_prompts.py

**File:** `scripts/validate_prompts.py`

**6 checks:**

| # | Check | Severity | What It Validates |
|---|-------|----------|-------------------|
| 1 | Prompt separation | ERROR | Each agent has an instruction of sufficient length |
| 2 | Prompt injection protections | WARNING | Instructions include safety boundary instructions |
| 3 | Secret leakage | ERROR | No API keys, passwords, or tokens in instruction strings |
| 4 | Unsupported placeholders | WARNING | Placeholder variables are documented and expected |
| 5 | Raw user interpolation | ERROR | No `user_*` variables in f-string prompts |
| 6 | Missing safety instructions | WARNING | Output guards and role establishment present |

---

## 6. validate_mcp.py

**File:** `scripts/validate_mcp.py`

**8 checks:**

| # | Check | Severity | What It Validates |
|---|-------|----------|-------------------|
| 1 | Authentication | WARNING | MCP servers have auth configuration |
| 2 | Authorization | WARNING | MCP servers scope exposed tools |
| 3 | Timeout | WARNING | MCP servers have timeout configuration |
| 4 | Retry | INFO | MCP servers have retry configuration |
| 5 | Versioning | INFO | MCP servers specify a version |
| 6 | Service abstraction | WARNING | MCP servers have a URL configured |
| 7 | No direct external API | ERROR | No HTTP imports in agents or tools (use MCP) |
| 8 | Tool registration | WARNING | MCP tools don't duplicate in-process tools |

---

## Extending Validators

The architecture supports adding new validators without modifying existing code.

### Adding a new validator script

```python
# scripts/validate_example.py
"""Validate example configurations."""
import sys
from dataclasses import dataclass

@dataclass
class Finding:
    field: str
    severity: str
    message: str
    file: str = ""
    line: int = 0

def main() -> int:
    findings: list[Finding] = []
    # ... validation logic ...
    errors = [f for f in findings if f.severity == "error"]
    for f in findings:
        tag = "FAIL" if f.severity == "error" else "WARN" if f.severity == "warning" else "INFO"
        print(f"  [{tag}] {f.field}: {f.message}")
    print(f"\nExample validation: {len(errors)} errors, {len(findings)} total")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
```

### Registering in pre-commit

Add to `.pre-commit-config.yaml`:
```yaml
  - repo: local
    hooks:
      - id: validate-example
        name: NN-validate-example
        entry: uv run python scripts/validate_example.py
        language: system
        pass_filenames: false
        always_run: true
        stages: [commit]
```

The `NN` prefix should match the stage position (e.g., `12-validate-example`).

### Error severity guidelines

| Severity | Blocks commit? | When to use |
|----------|---------------|-------------|
| `error` | Yes | Security violations, broken contracts, missing requirements |
| `warning` | No | Code quality, best practices, potential issues |
| `info` | No | Informational only, suggestions, statistics |

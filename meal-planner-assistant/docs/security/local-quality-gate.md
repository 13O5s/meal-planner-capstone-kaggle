# Local Quality & Security Gate

## Overview

The Local Quality & Security Gate runs 11 stages sequentially before every commit. It enforces the engineering rules, architecture standards, and security policies defined in `.agents/rules/` and `.agents/architecture/`.

## Execution Order

```
Stage  1: Ruff (lint + fix)           ─── fails → STOP
Stage  2: Ruff Format Check           ─── fails → STOP
Stage  3: detect-secrets              ─── fails → STOP
Stage  4: Semgrep                     ─── fails → STOP
Stage  5: validate_project.py         ─── fails → STOP
Stage  6: validate_workflow.py        ─── fails → STOP
Stage  7: validate_agents.py          ─── fails → STOP
Stage  8: validate_domain.py          ─── fails → STOP
Stage  9: validate_prompts.py         ─── fails → STOP
Stage 10: validate_mcp.py             ─── fails → STOP
Stage 11: pytest (fast tests)         ─── fails → STOP
```

### Stage 1 — Ruff (lint + fix)

**What it checks:**
- Unused imports (`F401`)
- Import ordering (`I001`)
- Pycodestyle errors (`E`)
- Pyflakes errors (`F`)
- Flake8-comprehensions (`C`)
- Flake8-bugbear (`B`)
- Pyupgrade (`UP`)
- Ruff-specific rules (`RUF`)

**Common failures:**
```
I001 Import block is un-sorted or un-formatted
F401 'module' imported but unused
```
**Fix:** `uv run ruff check --fix .` then `uv run ruff format .`

### Stage 2 — Ruff Format Check

**What it checks:**
- Line length (88 chars)
- Indentation consistency
- Trailing commas
- Blank line formatting

**Common failures:**
```
1 file would be reformatted
```
**Fix:** `uv run ruff format .`

### Stage 3 — detect-secrets

**What it checks:**
- High-entropy strings (potential API keys, tokens)
- Known secret patterns (AWS keys, private keys)
- Base64-encoded credentials

**Adding new secrets to baseline:**
```bash
# Scan a specific file to check
uv run detect-secrets scan --baseline .secrets.baseline path/to/file

# Update baseline with current state
uv run detect-secrets scan --baseline .secrets.baseline \
  --exclude-files "(uv\.lock|\.venv/|__pycache__/|\.git/|\.pytest_cache/)"

# Force update all
uv run detect-secrets scan --baseline .secrets.baseline --force-use-all-plugins \
  --exclude-files "(uv\.lock|\.venv/|__pycache__/|\.git/|\.pytest_cache/)"
```

**False positives:** If a flagged string is not a real secret, add it to `.secrets.baseline` by running the scan command. The baseline file is committed — it records known non-secrets so future scans don't flag them.

### Stage 4 — Semgrep

**What it checks (26 rules in 3 groups):**

**Group A — Secrets (10 rules, severity: ERROR)**
| Rule | Detects | Remediation |
|------|---------|-------------|
| `google-api-key` | Google API keys (`AIzaSy...`) | Store in `.env` as `GOOGLE_API_KEY` |
| `openai-api-key` | OpenAI keys (`sk-...`) | Store in `.env` |
| `anthropic-api-key` | Anthropic keys (`sk-ant-...`) | Store in `.env` |
| `aws-access-key` | AWS access keys (`AKIA...`) | Use IAM roles |
| `azure-connection-string` | Azure connection strings | Use managed identities |
| `jwt-secret` | JWT tokens (`eyJ...`) | Store in environment variables |
| `hardcoded-password` | `password="..."` assignments | Use env vars or secrets manager |
| `bearer-token` | Bearer tokens | Store in `.env` |
| `private-key-pattern` | `-----BEGIN PRIVATE KEY-----` | Use secrets manager |
| `service-account-key` | Service account JSON | Use workload identity |

**Group B — Dangerous Python (7 rules, severity: ERROR)**
| Rule | Detects | Safe alternative |
|------|---------|-----------------|
| `dangerous-eval` | `eval(...)` | `ast.literal_eval()` |
| `dangerous-exec` | `exec(...)` | Structured parser |
| `dangerous-pickle` | `pickle.loads(...)` | `json.loads()` / Pydantic |
| `dangerous-yaml-load` | `yaml.load(...)` | `yaml.safe_load()` |
| `dangerous-os-system` | `os.system(...)` | `subprocess.run([...])` |
| `dangerous-subprocess-shell` | `subprocess.run(..., shell=True)` | `shell=False` with list args |
| `dangerous-request-with-verify-false` | `verify=False` | Remove `verify=False` |

**Group C — ADK Architecture (9 rules, severity: ERROR)**
| Rule | Scope | What it enforces |
|------|-------|-----------------|
| `adk-agent-direct-api-call` | `app/agents/*.py` | No HTTP calls in agent factories |
| `adk-agent-gemini-client` | `app/agents/*.py` | No `Client()` in agents |
| `adk-business-logic-in-coordinator` | `app/agent.py` | No function defs in coordinator |
| `adk-sql-concatenation` | All Python | No string-concatenated SQL |
| `adk-http-in-agent` | `app/agents/*.py` | No HTTP imports in agent factories |
| `adk-raw-user-input-in-prompt` | All Python | No user vars in prompts |
| `adk-hardcoded-api-key-in-code` | All Python | No `api_key="..."` in .py |
| `adk-agent-bypass-service` | `app/agents/*.py`, `app/tools/*.py` | Route through services.py |
| `adk-agent-bypass-mcp` | All Python | Route through MCP |

**Adding custom Semgrep rules:**
Edit `.semgrep/rules.yaml` and add a new rule entry. See `docs/security/semgrep-rules.md` for details.

### Stage 5 — validate_project.py

**What it checks (12 validators):**

| # | Check | Severity | What it validates |
|---|-------|----------|-------------------|
| 1 | Agent registration | ERROR | All factories in app/agents/ registered in app/agent.py |
| 2 | Tool registration | ERROR | All tools in agent `tools=[]` exist in app/tools/ |
| 3 | Missing tests | WARNING | Each .py file has a corresponding test file |
| 4 | Circular imports | ERROR | No cycles in the app/ import graph |
| 5 | Hardcoded models | ERROR/WARN | Only `gemini-flash-latest` allowed |
| 6 | Hardcoded API keys | ERROR | No `api_key=` parameter in source code |
| 7 | Pydantic usage | WARNING | Models in app/models/ use BaseModel |
| 8 | Folder structure | ERROR | Required directories exist |
| 9 | Naming conventions | ERROR | snake_case files, test_ prefix for tests |
| 10 | Forbidden imports | ERROR | No `Dict`, `List`, `Optional`, `Tuple` from typing |
| 11 | Dependency direction | ERROR | Agents → tools → stores → models only |
| 12 | Unreferenced files | WARNING | Files not imported anywhere |

### Stage 6 — validate_workflow.py

**What it checks (9 validators):**

| # | Check | Severity | What it validates |
|---|-------|----------|-------------------|
| 1 | Orphan nodes | WARNING | All graph nodes are connected to an edge |
| 2 | Invalid graph edges | ERROR | Edges reference only defined nodes |
| 3 | Unexpected cycles | ERROR | Cycles only allowed for validation/retry loops |
| 4 | Security Checkpoint placement | ERROR | Every LLM node has a preceding SC node |
| 5 | Human-in-the-Loop placement | WARNING | HITL nodes follow deterministic output |
| 6 | Deterministic before LLM | ERROR | Business rules before LLM reasoning |
| 7 | Retry configuration | WARNING | LLM nodes have retry/fallback edges |
| 8 | Workflow metadata | WARNING | All required fields present |
| 9 | Coordinator completeness | WARNING | Instruction references all sub-agent tasks |

### Stage 7 — validate_agents.py

**What it checks (7 validators):**

| # | Check | Severity | What it validates |
|---|-------|----------|-------------------|
| 1 | Single responsibility | ERROR/WARN | Agent instruction matches domain keywords |
| 2 | Allowed tool usage | ERROR | Tools referenced exist in app/tools/ |
| 3 | Prompt separation | WARNING | Instructions are sufficiently descriptive |
| 4 | Prompt completeness | WARNING | Instructions document session state keys |
| 5 | Agent registration | ERROR | All agent factories referenced in coordinator |
| 6 | Shared memory usage | WARNING | Instructions reference session state |
| 7 | Context management | INFO | Callback/context parameter usage |

### Stage 8 — validate_domain.py

**What it checks (12 validators):**

**Meal Plan checks:**
- Calorie limits (800–3500 cal), Macro limits (protein ≤ 250g, carbs ≤ 500g, fat ≤ 150g)
- Allergy safety (known allergen tags), Dietary restrictions (valid dietary tags)
- Duplicate meals (no duplicate names), Meal diversity (2+ dietary tags across 3+ recipes)

**Shopping List checks:**
- Duplicate ingredients (no duplicate PRICE_DB keys)
- Ingredient reuse (cross-recipe coverage), Owned ingredient removal
- Cost estimation (references PRICE_DB)

**Recipe checks:**
- Normalized ingredients (normalize function works on recipe ingredients)
- Valid identifiers (recipe IDs and ingredient keys use valid format)

### Stage 9 — validate_prompts.py

**What it checks (6 validators):**

| # | Check | Severity | What it validates |
|---|-------|----------|-------------------|
| 1 | Prompt separation | ERROR | Each agent has an instruction of sufficient length |
| 2 | Prompt injection protections | WARNING | Safety boundary instructions present |
| 3 | Secret leakage | ERROR | No API keys or tokens in instruction strings |
| 4 | Unsupported placeholders | WARNING | Placeholder variables are documented |
| 5 | Raw user interpolation | ERROR | No `user_*` variables in f-string prompts |
| 6 | Missing safety instructions | WARNING | Output guards and role establishment |

### Stage 10 — validate_mcp.py

**What it checks (8 validators):**

| # | Check | Severity | What it validates |
|---|-------|----------|-------------------|
| 1 | Authentication | WARNING | MCP servers have auth configured |
| 2 | Authorization | WARNING | MCP servers scope exposed tools |
| 3 | Timeout | WARNING | MCP servers have timeout configured |
| 4 | Retry | INFO | MCP servers have retry configured |
| 5 | Versioning | INFO | MCP servers specify a version |
| 6 | Service abstraction | WARNING | MCP servers have a URL configured |
| 7 | No direct external API | ERROR | No HTTP imports in agents/tools (use MCP) |
| 8 | Tool registration | WARNING | MCP tools don't duplicate in-process tools |

### Stage 11 — pytest (fast tests only)

**What it runs:**
```bash
uv run pytest tests/unit -v --no-header -q -m "not integration and not e2e and not load"
```

**What is excluded:**
- `tests/integration/` — requires running server
- `tests/load_test/` — requires locust
- End-to-end tests — long running

**Pre-deployment test command (includes integration):**
```bash
uv run pytest tests/unit tests/integration
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| pre-commit not found | Not installed | `uv run pre-commit install` |
| detect-secrets fails with many findings | Baseline out of date | `uv run detect-secrets scan --baseline .secrets.baseline ...` |
| Semgrep fails on rules YAML | Syntax error in rules.yaml | `uv run semgrep --validate --config=.semgrep/rules.yaml` |
| Validator scripts crash unexpectedly | Missing dependency or import error | `uv sync --dev` |
| pytest fails but code is correct | Integration leak | Only `tests/unit` runs in pre-commit |
| pre-commit skips a hook | Hook misconfiguration | Check `.pre-commit-config.yaml` syntax |
| `validate_project.py` reports circular imports | New import added incorrectly | Check the import graph in the reported cycle |
| New validator not running | Not registered in pre-commit config | Add `- repo: local` hook entry |

## Skipping the Gate

If you need to skip the gate for a legitimate reason (e.g., WIP commit, CI-only change):
```bash
git commit --no-verify -m "message"
```

This should be rare. Document the reason in the commit message.

## Adding New Validation Rules (Future Validators)

The gate supports auto-discovery of future validators. Create a new file in `scripts/` with the naming convention `validate_*.py` and a `main() -> int` entry point:

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

Then add a new hook in `.pre-commit-config.yaml` at the correct position:
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

The `NN` prefix should match the stage number (e.g., `12-validate-example`).

## File Reference

| File | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | Hook definitions and execution order (11 stages) |
| `.semgrep/rules.yaml` | Custom Semgrep rules (26 rules, 3 groups) |
| `.semgrep/README.md` | Semgrep rule usage and extension guide |
| `.secrets.baseline` | Known non-secrets baseline for detect-secrets |
| `scripts/validate_project.py` | 12 structural project validators |
| `scripts/validate_workflow.py` | 9 workflow graph validators |
| `scripts/validate_agents.py` | 7 agent integrity validators |
| `scripts/validate_domain.py` | 12 domain model validators |
| `scripts/validate_prompts.py` | 6 prompt integrity validators |
| `scripts/validate_mcp.py` | 8 MCP configuration validators |
| `pyproject.toml` | Dev dependencies (ruff, semgrep, detect-secrets, pytest) |
| `docs/security/semgrep-rules.md` | Complete Semgrep rules reference |
| `docs/security/project-validation.md` | Complete validators reference |
| `.agents/rules/*.md` | Engineering rules enforced by the gate |
| `.agents/architecture/system-workflows.md` | Canonical workflow graph reference |

# Semgrep Rules Reference

This document catalogs all custom Semgrep rules used in the Local Quality & Security Gate.

## Rule Groups

| Group | Severity | Count | Scope |
|-------|----------|-------|-------|
| A — Secrets Detection | ERROR | 10 | All source files |
| B — Dangerous Python | ERROR | 7 | Python files only |
| C — ADK Architecture | ERROR | 9 | Agent/tool/service files |

Total: 26 rules

---

## Group A: Secrets Detection

All Group A rules block the commit with `ERROR` severity.

| # | Rule ID | Detects | Pattern |
|---|---------|---------|---------|
| 1 | `google-api-key` | Google API keys (AIzaSy...) | `pattern-regex` |
| 2 | `openai-api-key` | OpenAI keys (sk-...) | `pattern-regex` |
| 3 | `anthropic-api-key` | Anthropic keys (sk-ant-...) | `pattern-regex` |
| 4 | `aws-access-key` | AWS access keys (AKIA...) | `pattern-regex` |
| 5 | `azure-connection-string` | Azure connection strings | `pattern-regex` |
| 6 | `jwt-secret` | JWT tokens (eyJ...) | `pattern-regex` |
| 7 | `hardcoded-password` | password=`"..."` assignments | `pattern-regex` |
| 8 | `bearer-token` | Bearer tokens, auth tokens | `pattern-regex` |
| 9 | `private-key-pattern` | -----BEGIN PRIVATE KEY----- blocks | `pattern-regex` |
| 10 | `service-account-key` | Service account JSON keys | `pattern-regex` |

**Remediation for all secrets rules:**
1. Remove the hardcoded secret from the source file
2. Add it to `.env` (already gitignored)
3. Read via `os.getenv("VARIABLE_NAME")` at runtime

---

## Group B: Dangerous Python

All Group B rules block the commit with `ERROR` severity.

| # | Rule ID | Detects | Risk |
|---|---------|---------|------|
| 11 | `dangerous-eval` | `eval(...)` | Arbitrary code execution |
| 12 | `dangerous-exec` | `exec(...)` | Arbitrary code execution |
| 13 | `dangerous-pickle` | `pickle.loads(...)` / `pickle.load(...)` | Arbitrary deserialization |
| 14 | `dangerous-yaml-load` | `yaml.load(...)` | Arbitrary deserialization |
| 15 | `dangerous-os-system` | `os.system(...)` / `os.popen(...)` | Shell injection |
| 16 | `dangerous-subprocess-shell` | `subprocess.run(..., shell=True)` | Shell injection |
| 17 | `dangerous-request-with-verify-false` | `requests.get(url, verify=False)` | TLS bypass |

**Remediation:**

| Rule | Safe Alternative |
|------|-----------------|
| `eval()` / `exec()` | `ast.literal_eval()`, structured parser |
| `pickle.loads()` | `json.loads()`, `Pydantic.model_validate_json()` |
| `yaml.load()` | `yaml.safe_load()` |
| `os.system()` / `os.popen()` | `subprocess.run([...], shell=False)` |
| `subprocess.run(shell=True)` | `subprocess.run([...], shell=False)` |
| `verify=False` | Remove `verify=False` (defaults to `True`) |

---

## Group C: ADK Architecture Violations

All Group C rules block the commit with `ERROR` severity.

| # | Rule ID | Scope | What It Enforces |
|---|---------|-------|------------------|
| 18 | `adk-agent-direct-api-call` | `app/agents/*.py` | No HTTP calls inside agent factories |
| 19 | `adk-agent-gemini-client` | `app/agents/*.py` | No `Client()` instantiation in agents |
| 20 | `adk-business-logic-in-coordinator` | `app/agent.py` | No function defs in coordinator |
| 21 | `adk-sql-concatenation` | All Python | No string-concatenated SQL |
| 22 | `adk-http-in-agent` | `app/agents/*.py` | No HTTP imports in agent factories |
| 23 | `adk-raw-user-input-in-prompt` | All Python | No user vars in system prompts |
| 24 | `adk-hardcoded-api-key-in-code` | All Python | No `api_key="..."` in .py files |
| 25 | `adk-agent-bypass-service` | `app/agents/*.py`, `app/tools/*.py` | No cloud SDK calls (boto3, google.cloud, azure) outside services |
| 26 | `adk-agent-bypass-mcp` | All Python (excl. tools) | No HTTP calls outside tool functions — use MCP |

**Architecture rationale:**

ADK 2.0 enforces a strict layered architecture:
```
Agent (instruction only) → Tool (business logic) → MCP (external services)
```

Agents must never:
- Call APIs directly (must use Tools or MCP)
- Create model clients (ADK manages them)
- Contain business logic (must be in Tools)
- Interpolate user input into prompts (must use structured parameters)

---

## Running Rules

```bash
# Full scan
uv run semgrep --config=.semgrep/rules.yaml --error --no-autofix --metrics=off

# Validate rules syntax
uv run semgrep --validate --config=.semgrep/rules.yaml

# Single rule
uv run semgrep --config=.semgrep/rules.yaml --error --metrics=off --patterns --pattern 'eval($X)'
```

## Adding New Rules

1. Add entry to `.semgrep/rules.yaml` following existing format
2. Required fields: `id`, `message`, `severity`, `languages`
3. Add `fix` field with remediation guidance
4. Run `semgrep --validate` to check syntax
5. Update this document with the new rule
6. Commit (the new rule is active immediately)

## Rule Writing Patterns

| Use Case | Semgrep Construct |
|----------|-------------------|
| Regex match in source | `pattern-regex` |
| Exact function call | `pattern` |
| Call inside a function | `pattern-inside` + `pattern` |
| Multiple patterns (OR) | `patterns` + `pattern-either` |
| Scoped to files | `paths.include` / `paths.exclude` |

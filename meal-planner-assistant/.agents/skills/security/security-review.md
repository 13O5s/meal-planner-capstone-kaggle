# security-review

## Purpose
Conduct a comprehensive security review of the full application stack, covering authentication, authorization, logging, input/output validation, and data protection. This is a broader review than `code-security` — it covers architectural and operational security concerns across agents, tools, data stores, and deployment.

## When to Use
- Before deploying to production or sharing the application externally
- As part of a scheduled security audit (e.g., quarterly review)
- After significant architectural changes (new agent, new data store, new MCP server)
- After `code-security` review passes — this is the next level up

## Prerequisites
- `code-security` scan has been run and findings resolved
- Architecture documentation or `rules/architecture.md` is available
- List of all entry points: ADK agents, tool functions, API endpoints, CLI commands

## Inputs
- Full application source code (`app/` directory)
- Agent definitions and tool configurations
- Data store schemas and access patterns
- Deployment configuration (if available)

## Expected Outputs
- Security review report with findings across 6 categories:
  1. Authentication & Authorization
  2. Input & Output Validation
  3. Logging & Monitoring
  4. Data Protection
  5. Session Management
  6. Infrastructure Security
- Remediation plan with priority levels and estimated effort

## Step-by-Step Workflow

### 1. Authentication & Authorization
- Check if any agent or tool accepts user identity claims (user_id, role). If so, verify they are validated and not taken from untrusted input.
- Verify that tool access controls exist — not every agent should access every tool.
- Check for hardcoded tokens or API keys (delegate to `code-security` if not done yet).

### 2. Input & Output Validation
- Review each ADK tool function `parameters` in agent definitions. Verify that types, minimums, maximums, and patterns are specified.
- Review tool function implementations: do they validate input before using it?
- Check output: do agents or tools return sensitive data (user profiles with raw nutrition data, budget amounts) that shouldn't be exposed?
- Check for prompt injection: do any agents accept user input that gets interpolated directly into a Gemini prompt without sanitization?

### 3. Logging & Monitoring
- Verify no secrets or personal data are logged. Search for `logging` calls near variables that could contain sensitive values.
- Check that errors are logged with enough context to debug but not so much that they leak data.
- If `AGENTS.md` mentions monitoring or tracing, verify logging configuration follows those guidelines.

### 4. Data Protection
- Check session state: what data is stored and for how long? Are user profiles persisted in DuckDB? If so, verify no sensitive data (address, full name) is stored unnecessarily.
- Check if DuckDB is used with file-based persistence and whether the file is accessible to other users.
- Check for encryption: are any credentials stored in plaintext in data stores?

### 5. Session Management
- Review session state lifecycle: when is session state created, populated, and cleaned up? Is there a risk of session state leaking between users?
- Check for session state keys that could be overwritten by untrusted input.

### 6. Infrastructure Security
- If deployment config is available: check for open ports, exposed endpoints, CORS settings.
- Review dependency versions: are there known vulnerabilities in the dependency tree?

## Files to Create or Modify

| Action | File |
|--------|------|
| Read | All files in `app/` |
| Read | `pyproject.toml` or `requirements.txt` |
| Create | Security review report (output, not committed) |

## Validation Checklist
- [ ] All 6 categories reviewed
- [ ] Entry points (agents, tools, endpoints) identified and documented
- [ ] Finding includes: category, severity, file/line, description, impact, remediation
- [ ] False positives documented with justification
- [ ] Remediation plan includes priority and estimated effort

## Common Mistakes
- Only checking code — this review must cover architecture, data flow, and deployment too
- Ignoring the agent layer — security reviews often focus on web APIs and miss ADK agent input handling
- Treating all findings equally — prioritize by actual risk in the meal-planner context (budget data leak > theoretical SSRF)
- Not testing session isolation — in a multi-user deployment, session state must be scoped per user
- Forgetting about DuckDB file permissions — the database file must not be world-readable

## Related Rules
- `rules/security.md` — project-specific security policies
- `rules/architecture.md` — session state lifecycle, agent-to-tool access patterns
- `rules/coding.md` — input validation conventions

## Example Usage

```python
# Finding (HIGH) — Session Management / State Leak
# app/orchestrator.py:30
# Issue: Session state is a global dict, not scoped to user
_session_state: dict = {}  # BAD — shared across all users

# Remediation: Use a dict keyed by session_id
_sessions: dict[str, dict] = {}
session_state = _sessions.get(session_id, {})

# Finding (MEDIUM) — Input Validation / Prompt Injection
# app/agents/recipe.py:25
# Issue: User food preferences are interpolated directly into Gemini prompt
f"Recommend recipes that match these preferences: {user_input}"  # Potential injection

# Remediation: Use structured agent input, not raw string interpolation
```

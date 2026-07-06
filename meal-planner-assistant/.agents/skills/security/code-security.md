# code-security

## Purpose
Perform security review of Python code in the project, focusing on SQL injection, command injection, secret/key exposure, insecure deserialization, input validation, and dependency vulnerabilities. Output a prioritized list of findings with remediation steps.

## When to Use
- Before committing new code that handles user input, executes system commands, or accesses databases
- As part of PR review — run as a standalone check before requesting human review
- After adding new dependencies to `pyproject.toml` or `requirements.txt`
- When onboarding external contributions

## Prerequisites
- Python code files to review (target modules or entire `app/` directory)
- `rules/security.md` reviewed for project-specific security policies
- SAST tool installed if available: `pip install bandit` (recommended)

## Inputs
- Target file or directory path (e.g., `app/tools/`)
- Existing `rules/security.md` policies

## Expected Outputs
- Ordered list of security findings (severity: CRITICAL / HIGH / MEDIUM / LOW)
- For each finding: file, line, issue description, impact, and remediation code snippet
- Remediation code with before/after comparison

## Step-by-Step Workflow

1. **Run automated SAST scan**: If bandit is installed, run `bandit -r app/ -f json` and parse the output for findings. Filter by confidence (HIGH, MEDIUM) and severity (HIGH, MEDIUM, LOW) per bandit's classification.

2. **Manual pattern check**: Scan for the following patterns (prioritized):

   - **Secret/key exposure (CRITICAL)**: Search for hardcoded API keys, passwords, tokens, or connection strings. Look for patterns like `api_key = "`, `password = "`, `secret = "`, `os.environ["` without fallback handling. Any hardcoded credential must be flagged.
   - **SQL injection (CRITICAL)**: Search for f-string or `+` concatenation in SQL queries. DuckDB queries using `conn.execute(f"SELECT * FROM {user_input}")` must be flagged. Only parameterized queries accepted.
   - **Command injection (HIGH)**: Search for `os.system()`, `subprocess.call()`, `subprocess.Popen()` with user-controlled input. Flag if the command string is built from user input without sanitization.
   - **Insecure deserialization (HIGH)**: Search for `pickle.loads()`, `yaml.load()` (without `SafeLoader`), `eval()`, `exec()` with untrusted input.
   - **Path traversal (MEDIUM)**: Search for file path construction from user input without `os.path.abspath()` or `pathlib` validation to restrict to allowed directories.
   - **Input validation (MEDIUM)**: Check for user-facing inputs (agent parameters, tool arguments) that are not validated for type, range, or allowed values before being used.

3. **Check dependency vulnerabilities**: If `pip-audit` is available, run `pip-audit` on `pyproject.toml` or `requirements.txt`. Flag any known vulnerabilities in direct or transitive dependencies.

4. **Prioritize findings**: Order by severity (CRITICAL first). For each finding, provide:
   - The exact file and line number
   - A brief explanation of why it's a vulnerability
   - The potential impact in the context of meal-planner-assistant
   - A code snippet showing the fix

5. **Report**: Output the findings in a structured markdown format with CRITICAL/HIGH/MEDIUM/LOW sections.

## Files to Create or Modify

| Action | File |
|--------|------|
| Read | All files in `app/` directory |
| Create | Findings report (output, not committed) |

## Validation Checklist
- [ ] Automated SAST scan executed and findings extracted
- [ ] Manual checks cover all 6 categories (secrets, SQL injection, command injection, deserialization, path traversal, input validation)
- [ ] Dependency scan completed (or noted as unavailable)
- [ ] Findings prioritized by severity (CRITICAL first)
- [ ] Each finding has remediation code snippet
- [ ] False positives noted as such (e.g., test fixtures with mock keys)
- [ ] No findings dismissed without documented reason

## Common Mistakes
- Skipping automated SAST and only doing manual review — both are needed
- Flagging test mock data as secrets — label test credentials as false positives with justification
- Ignoring LOW severity findings — some LOW findings indicate deeper patterns (e.g., one hardcoded test key is LOW, but 50 suggest a systemic testing problem)
- Not providing remediation code — developers need a concrete fix, not just a warning
- Running bandit on virtual environment files — target only `app/` and `tests/`
- Forgetting to check for `yaml.load()` without `SafeLoader` — this is a common vector

## Related Rules
- `rules/security.md` — project-specific security policies, allowed patterns
- `rules/coding.md` — input validation and error handling conventions

## Example Usage

```python
# Finding (CRITICAL) — app/data/stores.py:42
# Issue: Hardcoded API key
api_key = "sk-1234567890abcdef"  # BAD

# Remediation:
api_key = os.environ.get("API_KEY")
if not api_key:
    raise ValueError("API_KEY environment variable not set")

# Finding (CRITICAL) — app/tools/db.py:15
# Issue: SQL injection via f-string
conn.execute(f"SELECT * FROM recipes WHERE name = '{user_input}'")  # BAD

# Remediation:
conn.execute("SELECT * FROM recipes WHERE name = ?", [user_input])
```

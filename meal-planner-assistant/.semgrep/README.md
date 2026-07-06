# Semgrep Rules — meal-planner-assistant

This directory contains custom Semgrep Community Edition rules for the meal-planner-assistant project.

## Rule Groups

| Group | Focus | Severity | Count |
|-------|-------|----------|-------|
| A — Secrets Detection | API keys, passwords, tokens, private keys, service accounts | ERROR | 10 |
| B — Dangerous Python | eval, exec, pickle, yaml.load, shell injection, TLS bypass | ERROR | 7 |
| C — ADK Violations | Architecture enforcement for ADK 2.0 agents | ERROR | 9 |

Total: 26 rules

## How to Run

```bash
# Run all rules against the project
uv run semgrep --config=.semgrep/rules.yaml --error --no-autofix --metrics=off

# Validate rules syntax
uv run semgrep --validate --config=.semgrep/rules.yaml

# Run a specific rule only
uv run semgrep --config=.semgrep/rules.yaml --error --metrics=off --patterns --pattern 'eval($X)'
```

## Adding Rules

1. Add a new `- id:` entry to `rules.yaml` following the existing format
2. Each rule must have:
   - `id` — unique, kebab-case identifier
   - `message` — human-readable description including the finding name
   - `severity` — ERROR or WARNING
   - `languages` — target language(s)
   - `fix` — remediation guidance (optional but recommended)
3. Run `uv run semgrep --validate --config=.semgrep/rules.yaml` to verify

## Rule Writing Tips

- Use `pattern-regex` for regex-based detection (secrets, patterns)
- Use `pattern` for exact AST matching (function calls, imports)
- Use `patterns` with `pattern-either` for OR conditions
- Use `pattern-inside` to scope rules to specific files or functions
- Use `paths.include`/`paths.exclude` to limit rule scope

## Integration

These rules run automatically via pre-commit (Stage 4: semgrep). See `docs/security/local-quality-gate.md`.

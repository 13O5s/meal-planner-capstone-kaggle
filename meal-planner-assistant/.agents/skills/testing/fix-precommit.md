# fix-precommit

## Purpose
Diagnose and resolve pre-commit hook failures systematically — identify which hook failed, apply the correct fix command, and re-run to confirm the issue is resolved.

## When to Use
- Pre-commit hooks fail during `git commit`
- A teammate's PR has pre-commit failures
- `.pre-commit-config.yaml` has been modified and hooks need adjustment
- CI pipeline reports lint/format failures

## Prerequisites
- `uv` is installed and available
- `.pre-commit-config.yaml` exists in the project root
- `uv run pre-commit run --all-files` can be executed from the project root
- `rules/coding.md` and `pyproject.toml` reviewed for project-specific lint configuration

## Inputs
- Pre-commit error output (console or CI log)
- List of files that failed

## Expected Outputs
- All pre-commit hooks pass (exit code 0)
- Files are fixed and re-staged for commit
- If unresolvable: documented explanation of why and alternative approach

## Step-by-Step Workflow

1. **Read the error output**: Identify which hook failed by reading the pre-commit console output. Common hooks and their markers:
   - `ruff` → lint/format errors
   - `gitleaks` → potential secret exposure
   - `codespell` → spelling mistakes
   - `trailing-whitespace` / `end-of-file-fixer` → whitespace issues

2. **Apply the correct fix per hook**:
   - **ruff check**: Run `uv run ruff check --fix .` then `uv run ruff format .`. Fixes: unused imports, deprecated typing, import sorting, style violations.
   - **ruff format**: Run `uv run ruff format .`. Fixes: indentation, line breaks, trailing commas.
   - **gitleaks**: Check for accidentally staged secrets. If a real secret, remove it from the file, update `.gitignore` if needed, and consider rotating the credential. If a false positive, add to `.gitleaksignore`.
   - **codespell**: Run `uv run codespell` to list all misspellings. Fix each in the source files.
   - **trailing-whitespace / end-of-file-fixer**: Run `uv run ruff format .` (handles both).

3. **Re-run hooks**: Execute `uv run pre-commit run --all-files`. Confirm exit code 0.

4. **Check persistent failures**: If a hook repeatedly fails, inspect `.pre-commit-config.yaml` for configuration issues (wrong repo URL, invalid rev, misconfigured args).

5. **Skip as last resort**: Only use `git commit --no-verify` when the failure is known to be a false positive and documented. Never use it to bypass genuine issues.

## Files to Create or Modify

| Action | File |
|--------|------|
| Modify | Any files flagged by pre-commit hooks |
| Read | `.pre-commit-config.yaml` — hook configuration |

## Validation Checklist
- [ ] `uv run pre-commit run --all-files` passes with exit code 0
- [ ] No secrets in staged files (gitleaks clean or false positive documented)
- [ ] No spelling errors (codespell clean)
- [ ] Ruff check + format both clean
- [ ] No use of `--no-verify` to bypass hooks

## Common Mistakes
- Using `--no-verify` to bypass hooks instead of fixing the underlying issue
- Running only `ruff check --fix` without `ruff format` afterward — this leaves formatting issues
- Ignoring gitleaks warnings without investigation — a real secret may be exposed
- Fixing only one file when multiple files are affected — run the fix command on the whole project
- Not running `ruff format` after `ruff check --fix` — `ruff check --fix` doesn't format, it only lints

## Related Rules
- `rules/coding.md` — style conventions enforced by ruff
- `rules/security.md` — gitleaks handling for secrets

## Example Usage

```bash
# Hook failed: ruff check
$ uv run pre-commit run --all-files
ruff.....................................................................Failed
  error: `app/tools/calculate_nutrition.py` has unused import `json`

# Fix:
$ uv run ruff check --fix .
$ uv run ruff format .
$ uv run pre-commit run --all-files
ruff.....................................................................Passed
```


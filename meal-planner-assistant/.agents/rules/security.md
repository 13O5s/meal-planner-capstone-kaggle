# Security Rules

## Purpose

Prevent exposure of secrets, API keys, and sensitive configuration in source code and version control.

## Principles

- Secrets must never appear in source files
- `.env` is the single source for environment-specific configuration
- The `.gitignore` already excludes `.env` — verify it stays excluded
- API keys must be read from environment variables, never hardcoded

## Required Practices

- Store all secrets in `.env` at the project root (already gitignored)
- Read secrets via `os.getenv("VARIABLE_NAME")` in `fast_api_app.py` (which calls `load_dotenv()`)
- For the Gemini API, the SDK reads `GOOGLE_API_KEY` from the environment automatically — do not pass `api_key` to the `Gemini()` constructor (it ignores it)
- Use environment variables for: `GOOGLE_API_KEY`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `LOGS_BUCKET_NAME`
- Run `gitleaks` via pre-commit to detect accidental secret commits

## Forbidden Practices

- Hardcoding API keys, passwords, or tokens in any `.py` file
- Committing `.env` files or real credentials
- Passing `api_key` as a parameter to `Gemini(model=...)` — the parameter is silently dropped by Pydantic
- Storing secrets in agent instruction strings or tool implementations

## Examples

```python
# Good: read from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Good: Gemini reads from env automatically
model = Gemini(model="gemini-flash-latest")

# Bad: hardcoded mock key (silently ignored)
model = Gemini(model="gemini-flash-latest", api_key="AIzaSy...")
```

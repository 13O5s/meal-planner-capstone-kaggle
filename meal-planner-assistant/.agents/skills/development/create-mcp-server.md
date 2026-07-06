# create-mcp-server

## Purpose
Create an external MCP (Model Context Protocol) server that exposes tools to agents via the MCP transport, with proper authentication, timeout, retry, and test coverage.

## When to Use
- Exposing an external API (recipe database, nutrition API, grocery pricing) as agent-callable tools
- Moving expensive computation out of the agent process
- Integrating with third-party services that require their own auth and lifecycle

## Prerequisites
- The MCP specification and project's `rules/mcp.md` have been reviewed
- Tool endpoints, input/output schemas, and authentication method are designed
- `rules/security.md` has been reviewed for credential and secret handling

## Inputs
- MCP server name
- List of exposed tools (name, input schema, output schema, description)
- Transport: `stdio` or HTTP with URL
- Authentication method: `none`, `api_key`, `oauth2`
- Timeout configuration (default seconds per request)
- Retry configuration (max retries, backoff strategy)

## Expected Outputs
- MCP server project directory with implementation
- Tool endpoints with input validation, timeout, and retry
- Authentication middleware
- Server configuration in project settings
- Unit tests for each tool's logic
- Integration tests for server startup and tool invocation

## Step-by-Step Workflow

1. **Scaffold MCP server**: Create the MCP server project directory following the MCP specification. Use the MCP SDK for the chosen language (Python recommended for consistency).

2. **Define exposed tools**: For each tool, create a handler function with:
   - Input validation (type checking, required fields, bounds)
   - Output schema (structured response with success/error fields)
   - Docstring describing the tool's purpose, inputs, and outputs

3. **Implement authentication**: Choose and implement the auth method:
   - **API key**: Read from environment variable, validate on every request
   - **OAuth2**: Implement token refresh flow, store tokens in memory
   - **None**: Only for local-only or development MCP servers
   - Follow `rules/security.md` — never hardcode credentials

4. **Implement timeout**: Set a configurable timeout per-tool-call using `asyncio.wait_for()` or HTTP client timeout. Default: 30 seconds. Make timeout configurable via environment variable.

5. **Implement retry**: Wrap external API calls with retry logic:
   - Max retries: configurable (default 2)
   - Backoff: exponential (1s, 2s, 4s) or constant
   - Retry on: network errors, 5xx responses, timeouts
   - Do not retry on: 4xx errors (client mistakes), validation failures

6. **Register services**: If the MCP server depends on shared services (recipe database, nutrition data), either:
   - Import and reuse from `app/services/` if running in-process
   - Connect to the same backend independently if running as a separate process

7. **Configure in project**: Add the MCP server configuration to the project's `opencode.json` or equivalent settings file. Reference environment variables for any secrets.

8. **Create unit tests**: Create `tests/unit/test_<server>_tools.py` covering each tool's logic in isolation. Mock external dependencies.

9. **Create integration tests**: Create `tests/integration/test_<server>.py` that starts the server, invokes each tool, and verifies responses. Use test-specific configuration (different ports, mock backends).

## Files to Create or Modify

| Action | File |
|--------|------|
| Create | `mcp-servers/<name>/` — MCP server project |
| Create | `mcp-servers/<name>/server.py` — main server |
| Create | `mcp-servers/<name>/tools.py` — tool handlers |
| Create | `mcp-servers/<name>/auth.py` — authentication |
| Create | `mcp-servers/<name>/config.py` — configuration |
| Modify | `opencode.json` or equivalent — MCP server registration |
| Modify | `.env.example` — MCP-related environment variables |
| Create | `tests/unit/test_<server>_tools.py` |
| Create | `tests/integration/test_<server>.py` |

## Validation Checklist
- [ ] Server starts and responds to MCP tool calls
- [ ] All tools have documented input/output schemas
- [ ] Authentication validates on every request
- [ ] Timeout interrupts long-running tool calls (configurable)
- [ ] Retry logic handles transient failures without infinite loops
- [ ] No secrets in MCP configuration files — all from environment variables
- [ ] Tools do not duplicate existing in-process tool functions
- [ ] `uv run pytest tests/unit/test_<server>_tools.py` passes
- [ ] `uv run pytest tests/integration/test_<server>.py` passes
- [ ] `agents-cli lint` passes on the MCP server code

## Common Mistakes
- Duplicating tools that already exist as in-process functions in `app/tools/`
- Hardcoding server URLs, API keys, or credentials in configuration files
- Forgetting to set timeouts — MCP server hangs forever on unresponsive backends
- Implementing retry on 4xx errors (client errors should fail fast)
- Creating an overly broad MCP server — prefer single-responsibility servers
- Not providing in-memory fallbacks for local development
- Exposing internal data paths or database schemas through MCP tool outputs

## Related Rules
- `rules/mcp.md` — MCP server standards, single responsibility, configuration
- `rules/security.md` — authentication, credentials from environment
- `rules/coding.md` — type annotations, code style for MCP server code
- `rules/testing.md` — unit and integration test patterns for server code

## Example Usage

```bash
# Input: MCP server "recipe-db" exposing two tools
#   search_recipes(ingredients: list[str]) -> list[recipe]
#   get_recipe_details(id: str) -> recipe
# Auth: API key from RECIPE_DB_API_KEY env var
# Timeout: 15s per call, retry 2x with 1s backoff

# Output:
#   mcp-servers/recipe-db/
#   ├── server.py
#   ├── tools.py
#   ├── auth.py
#   └── config.py
#   opencode.json — server registration
#   tests/unit/test_recipe_db_tools.py
#   tests/integration/test_recipe_db.py
```

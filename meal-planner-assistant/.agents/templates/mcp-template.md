# MCP Server Template: `<server_name>`

## Purpose
<!-- Describe what this MCP server provides. -->

## Location
<!-- Directory where the MCP server lives, e.g., `mcp-servers/<server_name>/` -->

## Tools Exposed

| Tool Name | Inputs | Outputs | Description |
|---|---|---|---|
| `<tool_1>` | `<param1>: type, <param2>: type` | `dict` with keys... | <description> |
| `<tool_2>` | ... | ... | ... |

## Configuration

In `opencode.json` or equivalent:

```json
{
  "mcp_servers": [
    {
      "name": "<server_name>",
      "url": "<transport_url>",
      "tools": ["<tool_1>", "<tool_2>"]
    }
  ]
}
```

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `<SERVER_VAR>` | <description> | Yes/No |
| `<API_KEY>` | <description> | Yes |

## In-Process Wrapper (optional)

If this MCP server exposes tools that should compose with in-process tools:

```python
# app/tools/<server_name>_wrapper.py
def <tool_function>(<params>) -> dict:
    """..."""
    # Call MCP server endpoint
    ...
```

## Validation

- [ ] Server starts and responds to all tool calls
- [ ] All tools have documented input/output schemas
- [ ] No secrets in MCP configuration files
- [ ] Credentials read from environment variables
- [ ] Tools do not duplicate existing in-process tools
- [ ] Configuration committed to version control

## Reference
- `rules/mcp.md` — MCP server standards
- `rules/security.md` — authentication and secret handling
- `skills/security/secure-mcp.md` — MCP security review workflow

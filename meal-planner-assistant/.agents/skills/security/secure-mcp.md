# secure-mcp

## Purpose
Audit and harden MCP (Model Context Protocol) server configurations against common security risks — hardcoded secrets, insecure transport, insufficient input validation, unauthorized data access, and missing rate limiting.

## When to Use
- Creating a new MCP server (review required as part of the creation workflow)
- Auditing existing MCP servers for security compliance
- After modifying an MCP server's tool implementations or authentication method
- Before deploying an MCP server to production

## Prerequisites
- MCP server source code or configuration files are accessible
- `rules/security.md` and `rules/mcp.md` have been reviewed
- Understanding of the MCP server's transport type (stdio vs HTTP) and authentication method

## Inputs
- MCP server configuration (e.g., opencode.json entries or MCP server source)
- Tool definitions and their network/file access patterns
- Authentication mechanism (none, API key, OAuth, mTLS)

## Expected Outputs
- Security audit report for the MCP server covering:
  1. Secret management
  2. Transport security
  3. Input validation
  4. Access control
  5. Rate limiting
  6. Data exposure
- Remediation steps for each finding

## Step-by-Step Workflow

1. **Audit secret management**: Check all MCP server configuration files and source code for hardcoded API keys, tokens, passwords, or connection strings. All credentials must come from environment variables. Flag any direct string literal that looks like a credential.

2. **Verify environment variable loading**: Confirm the MCP server reads credentials from `os.environ.get("VAR_NAME")` with proper error handling when the variable is missing. Check `.env.example` for documentation of all required variables.

3. **Review transport security**:
   - **HTTP transport**: Must use TLS in production. Check for `http://` (unsecured) vs `https://`. Verify the server does not bind to `0.0.0.0` unless behind a reverse proxy.
   - **stdio transport**: Verify the MCP server does not listen on any network port. stdio is inherently local — network exposure would defeat its security model.

4. **Review tool implementations**: For each tool exposed by the MCP server, verify:
   - All parameters are validated for type, range, and allowed values before processing
   - The tool does not execute arbitrary system commands or shell commands
   - The tool does not read/write files outside its allowed directory scope
   - The tool does not make network requests to user-controlled URLs

5. **Check access controls**: Each MCP tool should have the minimum necessary access. Tools should not be able to read configuration files, environment variables, or data belonging to other tools. Verify the MCP server does not expose tools that can access the host filesystem broadly.

6. **Check rate limiting**: For HTTP-transport MCP servers, verify rate limiting is configured to prevent abuse. For long-running or expensive operations, the MCP server should have timeout and concurrency limits.

7. **Verify data exposure**: Check that MCP tool responses do not return more data than necessary (e.g., returning full database contents when only a summary is needed).

## Files to Create or Modify

| Action | File |
|--------|------|
| Read | MCP server source code |
| Read | `opencode.json` or equivalent (MCP server list) |
| Read | `.env.example` — required environment variables |

## Validation Checklist
- [ ] No secrets in MCP configuration files or source code
- [ ] All credentials from environment variables with proper error handling
- [ ] Transport security verified (TLS for HTTP, no network on stdio)
- [ ] Tool inputs validated for type, range, and allowed values
- [ ] No tools execute dangerous system calls or access unrestricted paths
- [ ] Tools have least-privilege access to data
- [ ] Rate limiting configured (for HTTP transport)
- [ ] Tool responses do not over-share data

## Common Mistakes
- Hardcoding API keys in MCP server configuration or code
- Not validating tool inputs before processing them
- Exposing internal database or file paths through MCP tool outputs
- Using HTTP without TLS for production MCP servers
- Binding to `0.0.0.0` without authentication for HTTP-transport MCP
- Not configuring timeouts on MCP tool calls — long-running tools can block the server
- Assuming stdio MCP servers are safe without checking for network listeners

## Related Rules
- `rules/security.md` — project-wide security policies
- `rules/mcp.md` — MCP server creation conventions
- `rules/coding.md` — input validation standards

## Example Usage

```python
# Finding (CRITICAL) — Secret management
# MCP server config:
# BAD: Hardcoded API key
{
    "weather-mcp": {
        "command": "python",
        "args": ["mcp/weather.py"],
        "env": {
            "WEATHER_API_KEY": "abc123secretkey"  # BAD
        }
    }
}

# Remediation:
{
    "weather-mcp": {
        "command": "python",
        "args": ["mcp/weather.py"],
        "env": {
            "WEATHER_API_KEY": "${WEATHER_API_KEY}"  # GOOD — from environment
        }
    }
}

# Finding (HIGH) — Tool safety
# mcp/weather.py:
# Tool that accepts user-controlled URL:
def fetch_weather(url: str):  # BAD — user-controlled URL
    return requests.get(url)

# Remediation:
def fetch_weather(city: str):  # GOOD — only city name accepted
    base_url = "https://api.weather.com/v1"
    return requests.get(f"{base_url}/{city}")
```


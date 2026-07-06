# MCP Server Rules

## Purpose

Define standards for creating and maintaining MCP (Model Context Protocol) servers that extend agent capabilities.

## Principles

- MCP servers provide external tool capabilities to agents via the Model Context Protocol
- Each MCP server should have a single responsibility and a well-defined interface
- MCP servers are configured in the project's `opencode.json` or equivalent

## Required Practices

- Each MCP server must have a clear name and purpose
- Tools exposed via MCP must have documented inputs and outputs
- MCP server configuration must be committed to version control
- Use environment variables (from `.env`) for sensitive MCP configuration
- MCP servers must handle errors gracefully and return structured error responses

## Forbidden Practices

- Embedding secrets in MCP server configuration files
- Exposing tools that duplicate existing in-process tool functions
- MCP servers that make unauthenticated external API calls
- Creating MCP servers for logic that belongs in an agent or tool

## Examples

```json
{
  "mcp_servers": [
    {
      "name": "recipe-db",
      "url": "http://localhost:8081",
      "tools": ["search_recipes", "get_recipe_details"]
    }
  ]
}
```

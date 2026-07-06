import os

MCP_SERVER_NAME = "profile-mcp"
MCP_SERVER_VERSION = "0.1.0"
REQUEST_TIMEOUT = float(os.getenv("PROFILE_MCP_TIMEOUT", "30"))

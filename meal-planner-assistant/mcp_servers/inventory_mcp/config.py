import os

MCP_SERVER_NAME = "inventory-mcp"
MCP_SERVER_VERSION = "0.1.0"
REQUEST_TIMEOUT = float(os.getenv("INVENTORY_MCP_TIMEOUT", "30"))

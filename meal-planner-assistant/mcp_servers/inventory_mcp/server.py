import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_servers.inventory_mcp.tools import (
    get_inventory,
    normalize_ingredient,
    save_inventory,
)

# =====================================================================
# MCP SERVER: inventory-mcp
# Function: Serves ingredient inventory management tools over stdio protocol.
# Tools exposed:
#   - save_inventory: Standardizes and saves user ingredients list.
#   - get_inventory: Retrieves user's inventory ingredients.
#   - normalize_ingredient: Resolves raw ingredient names, quantities, and units.
# Security Features:
#   - Checks input validity of quantity fields.
#   - Restricts ingredients to known databases.
#   - Uses safe unit resolution maps.
# =====================================================================
server = Server("inventory-mcp")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="save_inventory",
            description="Save or update a user's ingredient inventory. Normalizes names and units automatically.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Unique user identifier"},
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit": {"type": "string"},
                                "available": {"type": "boolean"},
                            },
                            "required": ["name", "quantity", "unit"],
                        },
                    },
                },
                "required": ["user_id", "ingredients"],
            },
        ),
        Tool(
            name="get_inventory",
            description="Retrieve a user's saved ingredient inventory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Unique user identifier"},
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="normalize_ingredient",
            description="Normalize an ingredient name, resolve aliases, and check if it's known in the DB.",
            inputSchema={
                "type": "object",
                "properties": {
                    "raw_name": {"type": "string", "description": "Ingredient name (e.g. 'breast', 'chicken')"},
                    "raw_quantity": {"type": "number", "description": "Quantity (default 1.0)"},
                    "raw_unit": {"type": "string", "description": "Unit (e.g. 'g', 'piece', default 'piece')"},
                },
                "required": ["raw_name"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "save_inventory":
        result = save_inventory(arguments["user_id"], arguments["ingredients"])
    elif name == "get_inventory":
        result = get_inventory(arguments["user_id"])
    elif name == "normalize_ingredient":
        result = normalize_ingredient(
            arguments["raw_name"],
            arguments.get("raw_quantity", 1.0),
            arguments.get("raw_unit", "piece"),
        )
    else:
        raise ValueError(f"Unknown tool: {name}")

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_servers.profile_mcp.tools import get_profile, save_profile, validate_profile

# =====================================================================
# MCP SERVER: profile-mcp
# Function: Serves profile management tools over stdio protocol.
# Tools exposed:
#   - save_profile: Saves user profile details.
#   - get_profile: Retrieves saved profile details.
#   - validate_profile: Checks correctness of profile fields (age, height, weight, etc.)
# Security Features:
#   - Enforces data type checks (e.g. integer ages, string genders).
#   - Checks bounds: age [1, 150], height [50, 300], weight [10, 600].
#   - Constrains goals and genders to known enums.
# =====================================================================
server = Server("profile-mcp")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="save_profile",
            description="Save or update a user profile. Stores user_id -> profile_data mapping.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Unique user identifier"},
                    "profile_data": {
                        "type": "object",
                        "description": "Profile fields (age, gender, height_cm, weight_kg, goal, etc.)",
                    },
                },
                "required": ["user_id", "profile_data"],
            },
        ),
        Tool(
            name="get_profile",
            description="Retrieve a saved user profile by user ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Unique user identifier"},
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="validate_profile",
            description="Validate profile fields (age range, goal enum, etc) without saving.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile_data": {
                        "type": "object",
                        "description": "Profile data to validate",
                    },
                },
                "required": ["profile_data"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "save_profile":
        result = save_profile(arguments["user_id"], arguments["profile_data"])
    elif name == "get_profile":
        result = get_profile(arguments["user_id"])
    elif name == "validate_profile":
        result = validate_profile(arguments["profile_data"])
    else:
        raise ValueError(f"Unknown tool: {name}")

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

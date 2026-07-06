import json

import pytest
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters

pytestmark = pytest.mark.xfail(
    strict=False,
    reason="google-adk==2.2.0 passes `sampling_capabilities` to mcp SDK's ClientSession, "
    "but mcp==1.23.3 (pinned by semgrep) does not accept it. "
    "Upgrade semgrep or align mcp versions to enable this test.",
)


@pytest.fixture
async def inventory_toolset():
    params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "mcp_servers.inventory_mcp"],
        ),
        timeout=10.0,
    )
    toolset = McpToolset(connection_params=params)
    yield toolset
    await toolset.close()


async def test_list_tools(inventory_toolset):
    tools = await inventory_toolset.get_tools()
    tool_names = {t.name for t in tools}
    assert "save_inventory" in tool_names
    assert "get_inventory" in tool_names
    assert "normalize_ingredient" in tool_names


async def test_save_and_get_inventory(inventory_toolset):
    tools = await inventory_toolset.get_tools()
    save_tool = next(t for t in tools if t.name == "save_inventory")
    result = await save_tool.run_async(
        args={
            "user_id": "test-user-1",
            "ingredients": [{"name": "chicken breast", "quantity": 500, "unit": "g"}],
        },
        tool_context=None,
    )
    data = json.loads(result)
    assert data["saved"] is True
    assert data["count"] == 1

    get_tool = next(t for t in tools if t.name == "get_inventory")
    result = await get_tool.run_async(
        args={"user_id": "test-user-1"},
        tool_context=None,
    )
    data = json.loads(result)
    assert data["found"] is True
    assert data["ingredients"][0]["name"] == "chicken breast"


async def test_normalize_ingredient(inventory_toolset):
    tools = await inventory_toolset.get_tools()
    tool = next(t for t in tools if t.name == "normalize_ingredient")
    result = await tool.run_async(
        args={"raw_name": "breast", "raw_quantity": 200, "raw_unit": "g"},
        tool_context=None,
    )
    data = json.loads(result)
    assert data["name"] == "chicken breast"
    assert data["known"] is True
    assert data["quantity"] == 200

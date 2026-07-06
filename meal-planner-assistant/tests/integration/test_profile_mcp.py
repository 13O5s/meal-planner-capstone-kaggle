import json
import pytest
from mcp import StdioServerParameters
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams

pytestmark = pytest.mark.xfail(
    strict=False,
    reason="google-adk==2.2.0 passes `sampling_capabilities` to mcp SDK's ClientSession, "
    "but mcp==1.23.3 (pinned by semgrep) does not accept it. "
    "Upgrade semgrep or align mcp versions to enable this test.",
)


@pytest.fixture
async def profile_toolset():
    params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "mcp_servers.profile_mcp"],
        ),
        timeout=10.0,
    )
    toolset = McpToolset(connection_params=params)
    yield toolset
    await toolset.close()


async def test_list_tools(profile_toolset):
    tools = await profile_toolset.get_tools()
    tool_names = {t.name for t in tools}
    assert "save_profile" in tool_names
    assert "get_profile" in tool_names
    assert "validate_profile" in tool_names


async def test_save_and_get_profile(profile_toolset):
    tools = await profile_toolset.get_tools()
    save_tool = next(t for t in tools if t.name == "save_profile")
    result = await save_tool.run_async(
        args={"user_id": "test-user-1", "profile_data": {"age": 30, "goal": "healthy"}},
        tool_context=None,
    )
    data = json.loads(result)
    assert data["saved"] is True

    get_tool = next(t for t in tools if t.name == "get_profile")
    result = await get_tool.run_async(
        args={"user_id": "test-user-1"},
        tool_context=None,
    )
    data = json.loads(result)
    assert data["found"] is True
    assert data["profile"]["age"] == 30


async def test_validate_profile(profile_toolset):
    tools = await profile_toolset.get_tools()
    tool = next(t for t in tools if t.name == "validate_profile")
    result = await tool.run_async(
        args={"profile_data": {"age": 30, "goal": "healthy"}},
        tool_context=None,
    )
    data = json.loads(result)
    assert data["valid"] is True

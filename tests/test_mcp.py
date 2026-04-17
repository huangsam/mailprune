import pytest

from mailprune.mcp_server import mcp


@pytest.mark.asyncio
async def test_mcp_tool_registration():
    """Verify that all expected tools are registered with the MCP server."""
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]

    assert "audit" in tool_names
    assert "report" in tool_names
    assert "patterns" in tool_names
    assert "engagement" in tool_names
    assert "cluster" in tool_names


@pytest.mark.asyncio
async def test_mcp_tool_definitions():
    """Verify that tools have correct descriptions and arguments."""
    tools = await mcp.list_tools()

    audit_tool = next(t for t in tools if t.name == "audit")
    assert "Run an email audit" in audit_tool.description

    report_tool = next(t for t in tools if t.name == "report")
    assert "Generate a comprehensive email audit" in report_tool.description

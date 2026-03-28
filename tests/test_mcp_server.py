"""Tests for the MCP stdio server adapter."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from autoresearch.adapters.mcp_server import create_server


class TestCreateServer:
    """Test MCP server creation and tool registration."""

    def test_server_is_fastmcp_instance(self) -> None:
        server = create_server()
        assert isinstance(server, FastMCP)

    def test_server_name(self) -> None:
        server = create_server()
        assert server.name == "autoresearch"

    def test_has_autoresearch_run_tool(self) -> None:
        server = create_server()
        tools = server._tool_manager._tools
        assert "autoresearch_run" in tools

    def test_has_autoresearch_status_tool(self) -> None:
        server = create_server()
        tools = server._tool_manager._tools
        assert "autoresearch_status" in tools

    def test_has_autoresearch_read_report_tool(self) -> None:
        server = create_server()
        tools = server._tool_manager._tools
        assert "autoresearch_read_report" in tools

    def test_exactly_three_tools(self) -> None:
        server = create_server()
        tools = server._tool_manager._tools
        assert len(tools) == 3


class TestAutoresearchRunTool:
    """Test the autoresearch_run tool input/output."""

    @pytest.fixture
    def server(self) -> FastMCP:
        return create_server()

    @pytest.mark.asyncio
    async def test_run_requires_query(self, server: FastMCP) -> None:
        tool_fn = server._tool_manager._tools["autoresearch_run"].fn
        with pytest.raises(TypeError):
            await tool_fn()

    @pytest.mark.asyncio
    async def test_run_accepts_query(self, server: FastMCP) -> None:
        tool_fn = server._tool_manager._tools["autoresearch_run"].fn
        result = await tool_fn(query="What is Python?")
        assert isinstance(result, str)
        assert "task_id" in result or "error" in result

    @pytest.mark.asyncio
    async def test_run_accepts_depth(self, server: FastMCP) -> None:
        tool_fn = server._tool_manager._tools["autoresearch_run"].fn
        result = await tool_fn(query="What is Python?", depth="quick")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_run_rejects_invalid_depth(self, server: FastMCP) -> None:
        tool_fn = server._tool_manager._tools["autoresearch_run"].fn
        result = await tool_fn(query="What is Python?", depth="invalid")
        assert "error" in result.lower()


class TestAutoresearchStatusTool:
    """Test the autoresearch_status tool."""

    @pytest.fixture
    def server(self) -> FastMCP:
        return create_server()

    @pytest.mark.asyncio
    async def test_status_returns_string(self, server: FastMCP) -> None:
        tool_fn = server._tool_manager._tools["autoresearch_status"].fn
        result = await tool_fn()
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_status_with_task_id(self, server: FastMCP) -> None:
        tool_fn = server._tool_manager._tools["autoresearch_status"].fn
        result = await tool_fn(task_id="nonexistent")
        assert isinstance(result, str)
        assert "not found" in result.lower()


class TestAutoresearchReadReportTool:
    """Test the autoresearch_read_report tool."""

    @pytest.fixture
    def server(self) -> FastMCP:
        return create_server()

    @pytest.mark.asyncio
    async def test_read_report_requires_task_id(self, server: FastMCP) -> None:
        tool_fn = server._tool_manager._tools["autoresearch_read_report"].fn
        with pytest.raises(TypeError):
            await tool_fn()

    @pytest.mark.asyncio
    async def test_read_report_nonexistent_task(self, server: FastMCP) -> None:
        tool_fn = server._tool_manager._tools["autoresearch_read_report"].fn
        result = await tool_fn(task_id="nonexistent")
        assert isinstance(result, str)
        assert "not found" in result.lower()


class TestServerMain:
    """Test the run_server entry point."""

    def test_create_server_callable(self) -> None:
        from autoresearch.adapters.mcp_server import create_server as cs

        server = cs()
        assert callable(server.run)

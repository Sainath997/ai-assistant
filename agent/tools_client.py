"""
MCP tools client — connects to the local MCP server and exposes
each tool as a simple async Python function the agent loop can call.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPToolsClient:
    def __init__(self):
        self._session: ClientSession | None = None
        self._tools: dict = {}

    async def connect(self):
        """Start the MCP server subprocess and establish session."""
        params = StdioServerParameters(
            command="python",
            args=["-m", "mcp_server.server"],
        )
        self._transport = stdio_client(params)
        read, write = await self._transport.__aenter__()
        self._session = ClientSession(read, write)
        await self._session.__aenter__()
        await self._session.initialize()

        tools_result = await self._session.list_tools()
        self._tools = {t.name: t for t in tools_result.tools}

    async def disconnect(self):
        if self._session:
            await self._session.__aexit__(None, None, None)
        if self._transport:
            await self._transport.__aexit__(None, None, None)

    def available_tools(self) -> list[dict]:
        """Return tool schemas formatted for LLM function-calling."""
        schemas = []
        for name, tool in self._tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            })
        return schemas

    async def call(self, tool_name: str, arguments: dict) -> str:
        if not self._session:
            raise RuntimeError("MCPToolsClient not connected. Call connect() first.")
        result = await self._session.call_tool(tool_name, arguments)
        parts = [c.text for c in result.content if hasattr(c, "text")]
        return "\n".join(parts)

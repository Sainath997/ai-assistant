"""
MCP Server — exposes tools the AI agent can call:
  • web_search
  • read_file / write_file / list_directory
  • execute_code
  • remember / recall (memory)
  • calendar_list / calendar_add
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from mcp_server.tools.search import web_search
from mcp_server.tools.filesystem import read_file, write_file, list_directory
from mcp_server.tools.executor import execute_code
from mcp_server.tools.memory_tool import remember, recall
from mcp_server.tools.calendar_tool import calendar_list, calendar_add

app = Server("ai-assistant")

TOOLS: list[Tool] = [
    Tool(
        name="web_search",
        description="Search the web and return top results with titles, URLs, and snippets.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="read_file",
        description="Read the contents of a file at a given path.",
        inputSchema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    ),
    Tool(
        name="write_file",
        description="Write content to a file at a given path.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    ),
    Tool(
        name="list_directory",
        description="List files and folders in a directory.",
        inputSchema={
            "type": "object",
            "properties": {"path": {"type": "string", "default": "."}},
        },
    ),
    Tool(
        name="execute_code",
        description="Execute Python code in a sandboxed subprocess and return stdout/stderr.",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to run"},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["code"],
        },
    ),
    Tool(
        name="remember",
        description="Store a memory with an optional key so it can be recalled later.",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "key": {"type": "string", "description": "Optional label / tag"},
            },
            "required": ["content"],
        },
    ),
    Tool(
        name="recall",
        description="Recall memories relevant to a query using semantic search.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="calendar_list",
        description="List upcoming calendar events.",
        inputSchema={
            "type": "object",
            "properties": {"days_ahead": {"type": "integer", "default": 7}},
        },
    ),
    Tool(
        name="calendar_add",
        description="Add an event to the local calendar.",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start": {"type": "string", "description": "ISO 8601 datetime"},
                "end": {"type": "string", "description": "ISO 8601 datetime"},
                "description": {"type": "string"},
            },
            "required": ["title", "start", "end"],
        },
    ),
]


@app.list_tools()
async def handle_list_tools(request: ListToolsRequest) -> ListToolsResult:
    return ListToolsResult(tools=TOOLS)


@app.call_tool()
async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    name = request.params.name
    args = request.params.arguments or {}

    handlers = {
        "web_search": lambda: web_search(args["query"], args.get("max_results", 5)),
        "read_file": lambda: read_file(args["path"]),
        "write_file": lambda: write_file(args["path"], args["content"]),
        "list_directory": lambda: list_directory(args.get("path", ".")),
        "execute_code": lambda: execute_code(args["code"], args.get("timeout", 30)),
        "remember": lambda: remember(args["content"], args.get("key")),
        "recall": lambda: recall(args["query"], args.get("top_k", 5)),
        "calendar_list": lambda: calendar_list(args.get("days_ahead", 7)),
        "calendar_add": lambda: calendar_add(
            args["title"], args["start"], args["end"], args.get("description", "")
        ),
    }

    if name not in handlers:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")]
        )

    try:
        result = await handlers[name]()
        return CallToolResult(content=[TextContent(type="text", text=str(result))])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error in {name}: {e}")]
        )


async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

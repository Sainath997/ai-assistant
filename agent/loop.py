"""
Agentic loop — the core ReAct-style think → act → observe cycle.

Flow:
  1. Build prompt with system instructions + conversation history
  2. Ask LLM (with tool schemas injected)
  3. If LLM wants to call a tool → execute via MCP → append result → repeat
  4. When LLM produces a final text response → return it
"""

import json
import logging
from typing import AsyncIterator

from agent.llm import chat
from agent.tools_client import MCPToolsClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a highly capable personal AI assistant named Aria.
You have access to a set of tools that let you browse the web, read and write files,
run Python code, remember information across conversations, and manage calendar events.

Guidelines:
- Always think step-by-step before answering complex questions.
- Use tools whenever they will give a better, more accurate answer.
- After using a tool, summarise what you found before continuing.
- Be concise, friendly, and proactive.
- If you store something in memory, tell the user you've remembered it.
- Today's date/time is available via Python: use execute_code if you need it.
"""

MAX_ITERATIONS = 10  # safety cap on tool-call loops


async def run_agent(
    user_message: str,
    history: list[dict],
    mcp_client: MCPToolsClient,
) -> str:
    """
    Run one turn of the agentic loop.

    Args:
        user_message: The new user input.
        history:      Previous messages in OpenAI format.
        mcp_client:   Connected MCPToolsClient instance.

    Returns:
        The assistant's final response string.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    tools = mcp_client.available_tools()

    for iteration in range(MAX_ITERATIONS):
        response = await _llm_with_tools(messages, tools)

        # Check if the LLM wants to call a tool
        tool_calls = response.get("tool_calls")
        if tool_calls:
            # Append the assistant's tool-call message
            messages.append({"role": "assistant", **response})

            # Execute each tool call
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                fn_args = json.loads(tc["function"]["arguments"])
                logger.info("Tool call: %s(%s)", fn_name, fn_args)

                try:
                    result = await mcp_client.call(fn_name, fn_args)
                except Exception as e:
                    result = f"Tool error: {e}"

                logger.info("Tool result: %s", result[:200])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })
        else:
            # Final text response
            return response.get("content", "")

    return "I reached the maximum number of reasoning steps. Please try rephrasing."


async def _llm_with_tools(messages: list[dict], tools: list[dict]) -> dict:
    """
    Call the LLM and return a dict with either:
      { "content": "..." }                  — plain text
      { "tool_calls": [...], "content": "" } — tool invocations
    """
    from agent.config import settings
    provider = settings.llm_provider.lower()

    if provider == "openai":
        return await _openai_tool_call(messages, tools)
    else:
        # Anthropic / Ollama: inject tool descriptions into the system prompt
        return await _fallback_tool_call(messages, tools)


async def _openai_tool_call(messages: list[dict], tools: list[dict]) -> dict:
    from openai import AsyncOpenAI
    from agent.config import settings

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    msg = resp.choices[0].message
    if msg.tool_calls:
        return {
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        }
    return {"content": msg.content or ""}


async def _fallback_tool_call(messages: list[dict], tools: list[dict]) -> dict:
    """Simple JSON-based tool calling for providers without native support."""
    tool_desc = json.dumps(tools, indent=2)
    injection = f"""
You have access to the following tools. To call a tool respond ONLY with valid JSON:
{{"tool": "<tool_name>", "arguments": {{...}}}}

Tools:
{tool_desc}

If no tool is needed, respond normally in plain text.
"""
    augmented = list(messages)
    augmented[0] = {
        "role": "system",
        "content": augmented[0]["content"] + "\n\n" + injection,
    }

    raw = await chat(augmented)
    raw = raw.strip()

    if raw.startswith("{"):
        try:
            parsed = json.loads(raw)
            return {
                "tool_calls": [{
                    "id": "fallback_0",
                    "type": "function",
                    "function": {
                        "name": parsed["tool"],
                        "arguments": json.dumps(parsed.get("arguments", {})),
                    },
                }],
                "content": "",
            }
        except json.JSONDecodeError:
            pass

    return {"content": raw}

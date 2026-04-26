"""
Flexible LLM client — wraps OpenAI, Anthropic, and Ollama behind a single interface.
Switch providers by changing LLM_PROVIDER in .env.
"""

from typing import AsyncIterator
from agent.config import settings


async def chat_stream(messages: list[dict]) -> AsyncIterator[str]:
    """Yield response tokens as they arrive."""
    provider = settings.llm_provider.lower()

    if provider == "openai":
        yield await _openai_stream(messages)
    elif provider == "anthropic":
        yield await _anthropic_stream(messages)
    elif provider == "ollama":
        yield await _ollama_stream(messages)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


async def chat(messages: list[dict]) -> str:
    """Return the full response as a string."""
    provider = settings.llm_provider.lower()

    if provider == "openai":
        return await _openai_chat(messages)
    elif provider == "anthropic":
        return await _anthropic_chat(messages)
    elif provider == "ollama":
        return await _ollama_chat(messages)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


# ── OpenAI ──────────────────────────────────────────────────────────────────

async def _openai_chat(messages: list[dict]) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
    )
    return resp.choices[0].message.content or ""


async def _openai_stream(messages: list[dict]) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    chunks = []
    async with client.chat.completions.stream(
        model=settings.llm_model, messages=messages
    ) as stream:
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            chunks.append(delta)
    return "".join(chunks)


# ── Anthropic ────────────────────────────────────────────────────────────────

async def _anthropic_chat(messages: list[dict]) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_msgs = [m for m in messages if m["role"] != "system"]
    resp = await client.messages.create(
        model=settings.llm_model,
        max_tokens=4096,
        system=system,
        messages=user_msgs,
    )
    return resp.content[0].text


async def _anthropic_stream(messages: list[dict]) -> str:
    return await _anthropic_chat(messages)


# ── Ollama ───────────────────────────────────────────────────────────────────

async def _ollama_chat(messages: list[dict]) -> str:
    import httpx
    payload = {"model": settings.llm_model, "messages": messages, "stream": False}
    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120) as c:
        resp = await c.post("/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]


async def _ollama_stream(messages: list[dict]) -> str:
    return await _ollama_chat(messages)

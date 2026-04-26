"""Conversation summarization and long-term memory checkpointing."""

from agent.llm import chat
from agent.tools_client import MCPToolsClient


async def maybe_checkpoint_summary(
    session_id: str, history: list[dict], mcp_client: MCPToolsClient
) -> None:
    """Summarize long histories and store key points in memory."""
    if len(history) < 24:
        return

    last_slice = history[-24:]
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in last_slice)
    prompt = (
        "Summarize the conversation in <= 8 bullet points. "
        "Capture user preferences, commitments, and pending tasks.\n\n"
        f"{transcript}"
    )
    summary = await chat(
        [
            {"role": "system", "content": "You produce concise factual summaries."},
            {"role": "user", "content": prompt},
        ]
    )
    await mcp_client.call(
        "remember",
        {"content": f"Session {session_id} summary:\n{summary}", "key": f"session:{session_id}"},
    )

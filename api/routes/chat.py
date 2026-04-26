"""
Chat routes:
  POST /api/chat         — single-turn REST endpoint
  WS   /api/ws/chat      — streaming WebSocket endpoint
"""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from agent.loop import run_agent
from agent.storage import add_message, clear_session as clear_session_db, get_recent_messages
from agent.summarizer import maybe_checkpoint_summary
from api.security import enforce_rate_limit, enforce_rate_limit_for_key, require_api_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    request: Request,
    _: None = Depends(require_api_token),
):
    enforce_rate_limit(request)
    mcp_client = request.app.state.mcp_client
    history = await get_recent_messages(req.session_id)

    reply = await run_agent(req.message, history, mcp_client)

    await add_message(req.session_id, "user", req.message)
    await add_message(req.session_id, "assistant", reply)
    updated_history = await get_recent_messages(req.session_id)
    await maybe_checkpoint_summary(req.session_id, updated_history, mcp_client)

    return ChatResponse(reply=reply, session_id=req.session_id)


@router.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    await clear_session_db(session_id)
    return {"cleared": session_id}


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    mcp_client = websocket.app.state.mcp_client
    session_id = websocket.query_params.get("session_id", "ws_default")
    auth_token = websocket.query_params.get("token")

    # Enforce token auth for WS when configured.
    try:
        require_api_token(auth_token)
        client_key = websocket.client.host if websocket.client else "ws_unknown"
        enforce_rate_limit_for_key(client_key)
    except Exception:
        await websocket.send_json({"type": "error", "content": "Unauthorized or rate-limited"})
        await websocket.close(code=1008)
        return

    history = await get_recent_messages(session_id)

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_message = payload.get("message", "")

            await websocket.send_json({"type": "thinking"})

            try:
                reply = await run_agent(user_message, history, mcp_client)
            except Exception as e:
                logger.exception("Agent error")
                reply = f"Sorry, something went wrong: {e}"

            await add_message(session_id, "user", user_message)
            await add_message(session_id, "assistant", reply)
            history = await get_recent_messages(session_id)
            await maybe_checkpoint_summary(session_id, history, mcp_client)

            await websocket.send_json({"type": "message", "content": reply})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session_id)

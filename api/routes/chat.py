"""
Chat routes:
  POST /api/chat         — single-turn REST endpoint
  WS   /api/ws/chat      — streaming WebSocket endpoint
"""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from agent.loop import run_agent

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

# In-memory session store  {session_id: [messages]}
_sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, request: Request):
    mcp_client = request.app.state.mcp_client
    history = _sessions.setdefault(req.session_id, [])

    reply = await run_agent(req.message, history, mcp_client)

    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})

    # Keep last 40 messages to avoid runaway context
    _sessions[req.session_id] = history[-40:]

    return ChatResponse(reply=reply, session_id=req.session_id)


@router.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"cleared": session_id}


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    mcp_client = websocket.app.state.mcp_client
    session_id = "ws_default"
    history = _sessions.setdefault(session_id, [])

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

            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": reply})
            _sessions[session_id] = history[-40:]

            await websocket.send_json({"type": "message", "content": reply})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session_id)

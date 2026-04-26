"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from agent.config import settings
from agent.storage import init_db
from agent.tools_client import MCPToolsClient
from api.routes import chat, health

mcp_client = MCPToolsClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await mcp_client.connect()
    app.state.mcp_client = mcp_client
    yield
    await mcp_client.disconnect()


app = FastAPI(
    title="AI Assistant",
    description="Agentic AI Assistant powered by MCP",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# Serve the React UI from /ui/dist if it exists
ui_dist = Path(__file__).parent.parent / "ui" / "dist"
if ui_dist.exists():
    app.mount("/", StaticFiles(directory=str(ui_dist), html=True), name="ui")

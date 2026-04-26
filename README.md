# AI Assistant — Aria

A fully agentic personal AI assistant powered by **MCP (Model Context Protocol)**, FastAPI, and React.

## Features

| Capability | Description |
|---|---|
| 🔍 Web Search | DuckDuckGo search, no API key needed |
| 📁 File System | Read/write/browse with root-path restrictions |
| 🐍 Code Execution | Sandboxed Python execution with timeout + restricted operations |
| 🧠 Memory | Persistent vector memory via ChromaDB |
| 📅 Calendar | Local ICS + optional CalDAV/Google-compatible calendars |
| 💬 Chat UI | Modern streaming React chat interface |
| 🔀 Flexible LLM | OpenAI · Anthropic · Ollama — swap via `.env` |
| 🔐 Safety | Optional API token auth + per-client rate limiting |

## Architecture

```
┌─────────────┐     WebSocket      ┌──────────────────┐
│  React UI   │ ◄────────────────► │  FastAPI Backend │
│  (Vite)     │                    │  /api/ws/chat    │
└─────────────┘                    └────────┬─────────┘
                                            │
                                    ┌───────▼────────┐
                                    │  Agent Loop    │
                                    │  (ReAct style) │
                                    └───────┬────────┘
                                            │ tool calls
                                    ┌───────▼────────┐
                                    │   MCP Server   │
                                    │  (stdio)       │
                                    └───────┬────────┘
                         ┌──────────────────┼──────────────────┐
                    web_search        execute_code         remember/recall
                    read/write_file   calendar_list/add
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/Sainath997/ai-assistant.git
cd ai-assistant

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set LLM_PROVIDER and your API key
```

Optional hardening:
- Set `API_TOKEN` to require auth for chat requests.
- Set `FILESYSTEM_ROOT` to limit file access to a safe directory.
- Configure `CALDAV_*` values to connect a remote calendar.

### 3. Run

```bash
chmod +x start.sh
./start.sh
```

Open **http://localhost:5173** and start chatting with Aria!

## Switching LLM Providers

Edit `.env`:

```env
# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...

# Ollama (local, free)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

## Project Structure

```
ai-assistant/
├── mcp_server/          # MCP server + all tool implementations
│   └── tools/
│       ├── search.py
│       ├── filesystem.py
│       ├── executor.py
│       ├── memory_tool.py
│       └── calendar_tool.py
├── agent/               # Agent core
│   ├── config.py        # Settings from .env
│   ├── llm.py           # LLM provider abstraction
│   ├── storage.py       # SQLite chat persistence
│   ├── summarizer.py    # Conversation checkpoint summaries
│   ├── tools_client.py  # MCP client
│   └── loop.py          # ReAct agentic loop
├── api/                 # FastAPI backend
│   ├── security.py      # API token + rate limiting
│   └── routes/
│       ├── chat.py      # REST + WebSocket endpoints
│       └── health.py
├── ui/                  # React + Vite frontend
│   └── src/
│       ├── App.tsx
│       ├── hooks/useChat.ts
│       └── components/
├── memory/              # Persisted data (gitignored)
├── main.py              # Backend entry point
├── start.sh             # Start both servers
└── requirements.txt
```

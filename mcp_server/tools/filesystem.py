"""File system tools: read, write, list directory."""

import aiofiles
from pathlib import Path

from agent.config import settings


_ROOT = Path(settings.filesystem_root).expanduser().resolve()


def _resolve_in_root(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = _ROOT / candidate
    resolved = candidate.resolve()
    if _ROOT not in resolved.parents and resolved != _ROOT:
        raise ValueError(f"Access denied outside allowed root: {_ROOT}")
    return resolved


async def read_file(path: str) -> str:
    p = _resolve_in_root(path)
    if not p.exists():
        return f"Error: file not found — {path}"
    async with aiofiles.open(p, "r", encoding="utf-8", errors="replace") as f:
        return await f.read()


async def write_file(path: str, content: str) -> str:
    p = _resolve_in_root(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(p, "w", encoding="utf-8") as f:
        await f.write(content)
    return f"Written {len(content)} characters to {p}"


async def list_directory(path: str = ".") -> str:
    p = _resolve_in_root(path)
    if not p.exists():
        return f"Error: path not found — {path}"
    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name))
    lines = []
    for entry in entries:
        icon = "📄" if entry.is_file() else "📁"
        lines.append(f"{icon} {entry.name}")
    return "\n".join(lines) if lines else "(empty directory)"

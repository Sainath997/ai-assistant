"""File system tools: read, write, list directory."""

import aiofiles
from pathlib import Path


async def read_file(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: file not found — {path}"
    async with aiofiles.open(p, "r", encoding="utf-8", errors="replace") as f:
        return await f.read()


async def write_file(path: str, content: str) -> str:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(p, "w", encoding="utf-8") as f:
        await f.write(content)
    return f"Written {len(content)} characters to {p}"


async def list_directory(path: str = ".") -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: path not found — {path}"
    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name))
    lines = []
    for entry in entries:
        icon = "📄" if entry.is_file() else "📁"
        lines.append(f"{icon} {entry.name}")
    return "\n".join(lines) if lines else "(empty directory)"

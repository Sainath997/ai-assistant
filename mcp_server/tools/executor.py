"""Code execution tool — runs Python in a subprocess sandbox."""

import asyncio
import sys
import tempfile
from pathlib import Path


async def execute_code(code: str, timeout: int = 30) -> str:
    blocked = ["import os", "import subprocess", "open(", "__import__", "eval(", "exec("]
    lowered = code.lower()
    if any(tok in lowered for tok in blocked):
        return "Error: code contains restricted operations."

    safe_timeout = max(1, min(timeout, 15))
    with tempfile.TemporaryDirectory() as tmpdir:
        script = Path(tmpdir) / "snippet.py"
        script.write_text(code, encoding="utf-8")
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=tmpdir,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=safe_timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return f"Error: execution timed out after {safe_timeout}s"

    output = ""
    if stdout:
        output += f"STDOUT:\n{stdout.decode()}"
    if stderr:
        output += f"\nSTDERR:\n{stderr.decode()}"
    if proc.returncode != 0:
        output += f"\nExit code: {proc.returncode}"
    return output.strip() or "(no output)"

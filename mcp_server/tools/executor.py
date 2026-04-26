"""Code execution tool — runs Python in a subprocess sandbox."""

import asyncio
import sys


async def execute_code(code: str, timeout: int = 30) -> str:
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-c", code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return f"Error: execution timed out after {timeout}s"

    output = ""
    if stdout:
        output += f"STDOUT:\n{stdout.decode()}"
    if stderr:
        output += f"\nSTDERR:\n{stderr.decode()}"
    if proc.returncode != 0:
        output += f"\nExit code: {proc.returncode}"
    return output.strip() or "(no output)"

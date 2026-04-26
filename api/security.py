"""API auth and lightweight in-memory rate limiting."""

from collections import defaultdict, deque
from time import time

from fastapi import Header, HTTPException, Request, status

from agent.config import settings

_bucket: dict[str, deque[float]] = defaultdict(deque)


def _get_client_id(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def require_api_token(x_api_token: str | None = Header(default=None)) -> None:
    """Validate API token when configured.

    If API_TOKEN is empty, auth is disabled for local development.
    """
    if not settings.api_token:
        return
    if x_api_token != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token.",
        )


def enforce_rate_limit(request: Request) -> None:
    """Simple fixed-window rate limit per client."""
    enforce_rate_limit_for_key(_get_client_id(request))


def enforce_rate_limit_for_key(key: str) -> None:
    """Simple fixed-window rate limit for an arbitrary client key."""
    limit = max(1, settings.rate_limit_per_minute)
    now = time()
    window_start = now - 60
    q = _bucket[key]

    while q and q[0] < window_start:
        q.popleft()

    if len(q) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({limit}/min).",
        )
    q.append(now)

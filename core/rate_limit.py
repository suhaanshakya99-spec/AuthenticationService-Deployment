import time
import asyncio
from fastapi import HTTPException
from core.config import settings

"""
In-memory replacement for the old Redis-backed rate limiter.

This works as a simple fixed-window counter kept in a process-local
dict. It's a drop-in behavioural equivalent for a single-process local
setup: each key (e.g. an email) gets a counter that resets after
`settings.TIMEFRAME` seconds, and requests are rejected once the
counter passes `settings.LIMIT`.

NOTE: because this state lives in memory, it resets whenever the
server restarts and is per-process (won't share counts across
multiple uvicorn workers). That's fine for local/dev use; if this
service is ever run with multiple workers or multiple instances,
swap this back for a shared store (e.g. Redis) instead.
"""

_buckets: dict[str, dict[str, float | int]] = {}
_lock = asyncio.Lock()


async def ratelimiting(email: str):
    key = f"email:{email}"
    now = time.monotonic()

    async with _lock:
        bucket = _buckets.get(key)

        if bucket is None or now >= bucket["reset_at"]:
            bucket = {"count": 0, "reset_at": now + settings.TIMEFRAME}
            _buckets[key] = bucket

        bucket["count"] += 1
        count = bucket["count"]

    if count > settings.LIMIT:
        print(f"{email}'s number of request = {count}")
        raise HTTPException(status_code=429, detail="too many requests")

"""Async Redis pub/sub client, shared across requests in this service."""

import os

import redis.asyncio as aioredis

REDIS_URL = os.environ.get("REDIS_URL", "")

_client: "aioredis.Redis | None" = None


def get_client() -> "aioredis.Redis":
    global _client
    if not REDIS_URL:
        raise RuntimeError("REDIS_URL is not set")
    if _client is None:
        _client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _client


# Generic reference-counted "someone wants this" signal, shared by both
# /stream/prices (desired_set="watch:desired", consumed by
# marketdata/router.py's sync_watched_symbols, Workstream 3) and
# /stream/signals (desired_set="engine:desired", consumed by app.py's engine
# worker, Workstream 5). `{desired_set}` holds every currently-wanted value;
# `{desired_set}:refcount:{value}` tracks how many viewers so the set entry
# is only dropped once the last one disconnects.
async def mark_wanted(desired_set: str, value: str) -> None:
    client = get_client()
    await client.sadd(desired_set, value)
    await client.incr(f"{desired_set}:refcount:{value}")


async def mark_unwanted(desired_set: str, value: str) -> None:
    client = get_client()
    count = await client.decr(f"{desired_set}:refcount:{value}")
    if count <= 0:
        await client.srem(desired_set, value)
        await client.delete(f"{desired_set}:refcount:{value}")

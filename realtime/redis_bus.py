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

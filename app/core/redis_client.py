"""
Redis client for caching orders. TTL from config.
"""
import json
from uuid import UUID

import redis.asyncio as redis

from app.config import settings
from app.schemas.order import OrderResponse


def _order_key(order_id: UUID) -> str:
    return f"order:{order_id}"


class RedisOrderCache:
    """Cache orders in Redis with TTL."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._ttl = settings.order_cache_ttl_seconds

    async def connect(self) -> None:
        if self._client is None:
            self._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_order(self, order_id: UUID) -> OrderResponse | None:
        """Get order from cache. Returns None if miss or error."""
        await self.connect()
        if not self._client:
            return None
        try:
            data = await self._client.get(_order_key(order_id))
            if not data:
                return None
            return OrderResponse.model_validate_json(data)
        except Exception:
            return None

    async def set_order(self, order: OrderResponse) -> None:
        """Set order in cache with TTL."""
        await self.connect()
        if not self._client:
            return
        try:
            key = _order_key(order.id)
            await self._client.set(
                key,
                order.model_dump_json(),
                ex=self._ttl,
            )
        except Exception:
            pass

    async def delete_order(self, order_id: UUID) -> None:
        """Invalidate cache on update."""
        await self.connect()
        if not self._client:
            return
        try:
            await self._client.delete(_order_key(order_id))
        except Exception:
            pass


redis_order_cache = RedisOrderCache()

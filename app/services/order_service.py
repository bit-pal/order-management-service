"""
Order service: create, get (cache-first), update status, list by user.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rabbitmq import publish_new_order
from app.core.redis_client import redis_order_cache
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate


async def create_order(db: AsyncSession, user_id: int, payload: OrderCreate) -> Order:
    """Create order, publish new_order event to RabbitMQ. Returns created order."""
    items_data = [item.model_dump() for item in payload.items]
    order = Order(
        user_id=user_id,
        items=items_data,
        total_price=payload.total_price,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)
    await publish_new_order(order.id)
    return order


async def get_order_by_id(db: AsyncSession, order_id: UUID) -> Order | None:
    """Get order from DB by id."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def get_order_cached(db: AsyncSession, order_id: UUID) -> OrderResponse | None:
    """Get order: first from Redis cache, then from DB. Updates cache on DB hit."""
    cached = await redis_order_cache.get_order(order_id)
    if cached is not None:
        return cached
    order = await get_order_by_id(db, order_id)
    if order is None:
        return None
    response = OrderResponse.model_validate(order)
    await redis_order_cache.set_order(response)
    return response


async def update_order_status(
    db: AsyncSession,
    order_id: UUID,
    payload: OrderStatusUpdate,
) -> Order | None:
    """Update order status. Invalidates cache."""
    order = await get_order_by_id(db, order_id)
    if order is None:
        return None
    order.status = payload.status
    await db.flush()
    await db.refresh(order)
    await redis_order_cache.delete_order(order_id)
    return order


async def get_orders_by_user_id(db: AsyncSession, user_id: int) -> list[Order]:
    """Get all orders for user (from DB)."""
    result = await db.execute(
        select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())

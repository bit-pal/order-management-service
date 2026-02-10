"""
Orders API: create, get by id (cache-first), patch status, get by user_id.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.order_service import (
    create_order,
    get_order_cached,
    get_orders_by_user_id,
    update_order_status,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order_endpoint(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Create order (authorized only). Publishes new_order to event-bus."""
    order = await create_order(db, current_user.id, payload)
    return OrderResponse.model_validate(order)


@router.get("/{order_id}/", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Get order by id. Served from Redis cache when available (TTL 5 min)."""
    order_response = await get_order_cached(db, order_id)
    if order_response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if order_response.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this order",
        )
    return order_response


@router.patch("/{order_id}/", response_model=OrderResponse)
async def patch_order(
    order_id: UUID,
    payload: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Update order status. Cache is invalidated."""
    order = await update_order_status(db, order_id, payload)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update this order",
        )
    return OrderResponse.model_validate(order)


@router.get("/user/{user_id}/", response_model=list[OrderResponse])
async def get_orders_by_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    """Get all orders for user. Only own user_id allowed."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to list other user orders",
        )
    orders = await get_orders_by_user_id(db, user_id)
    return [OrderResponse.model_validate(o) for o in orders]

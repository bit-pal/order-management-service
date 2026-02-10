"""Order-related Pydantic schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


class OrderItem(BaseModel):
    """Single item in order (for JSON items)."""

    name: str
    quantity: int = 1
    price: float


class OrderCreate(BaseModel):
    """Payload for creating an order."""

    items: list[OrderItem] = Field(..., min_length=1)
    total_price: float = Field(..., gt=0)


class OrderStatusUpdate(BaseModel):
    """Payload for PATCH order status."""

    status: OrderStatus


class OrderResponse(BaseModel):
    """Order in API response."""

    id: UUID
    user_id: int
    items: list
    total_price: float
    status: OrderStatus
    created_at: datetime

    model_config = {"from_attributes": True}

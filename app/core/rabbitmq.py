"""
RabbitMQ publisher (event-bus). Publishes new_order events.
"""
import json
from uuid import UUID

import aio_pika
from aio_pika import Message

from app.config import settings


async def publish_new_order(order_id: UUID) -> None:
    """
    Publish new_order event to RabbitMQ queue.
    Consumer will pick it up and trigger Celery task.
    """
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(settings.rabbitmq_queue, durable=True)
            body = json.dumps({"order_id": str(order_id)}).encode()
            await channel.default_exchange.publish(
                Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=settings.rabbitmq_queue,
            )
    except Exception:
        # Log and re-raise or swallow depending on requirements
        raise

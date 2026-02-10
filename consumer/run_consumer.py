"""
RabbitMQ consumer (separate process). Subscribes to new_orders queue,
receives events and triggers Celery task process_order.
"""
import asyncio
import json
import sys

import aio_pika

# Ensure project root is on path
sys.path.insert(0, ".")

from app.config import settings
from celery_app.tasks import process_order


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(settings.rabbitmq_queue, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                        order_id = body.get("order_id")
                        if order_id:
                            process_order.delay(order_id)
                    except Exception:
                        pass


if __name__ == "__main__":
    asyncio.run(main())

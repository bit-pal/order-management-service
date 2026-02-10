"""
Celery tasks. process_order: background processing (sleep 2s, print).
"""
import time
from uuid import UUID

from celery_app import celery_app


@celery_app.task(name="process_order")
def process_order(order_id: str) -> None:
    """Background task: simulate processing (2s) and log."""
    time.sleep(2)
    print(f"Order {order_id} processed")

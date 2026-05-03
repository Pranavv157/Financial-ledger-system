

from celery import shared_task
from .services import transfer_funds
from .redis_client import redis_client


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_transfer(self, sender_id, receiver_id, amount, reference_id):

    lock_key = f"lock:transfer:{reference_id}"

    #  try to acquire lock
    acquired = redis_client.set(lock_key, "1", nx=True, ex=30)

    if not acquired:
        # another worker is already processing
        return "Already processing"

    try:
        return transfer_funds(sender_id, receiver_id, amount, reference_id)

    finally:
        #  release lock
        redis_client.delete(lock_key)
    return {
        "transaction_id": txn.id,
        "reference_id": txn.reference_id,
        "status": txn.status,
    }
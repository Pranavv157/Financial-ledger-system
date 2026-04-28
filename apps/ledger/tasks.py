from celery import shared_task
from django.db import OperationalError
from .services import transfer_funds

@shared_task(
    bind=True,
    autoretry_for=(OperationalError,),  # only retry DB connectivity issues
    retry_backoff=True,
    max_retries=3
)
def process_transfer(self, sender_id, receiver_id, amount, reference_id):
    return transfer_funds(sender_id, receiver_id, amount, reference_id)

    return {
        "transaction_id": txn.id,
        "reference_id": txn.reference_id,
        "status": txn.status,
    }
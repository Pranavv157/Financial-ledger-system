from celery import shared_task
from django.db import IntegrityError
from decimal import Decimal

from apps.ledger.models import Transaction
from apps.ledger.exceptions import InsufficientFundsError
from .services import transfer_funds


@shared_task(bind=True, autoretry_for=(IntegrityError,), retry_backoff=True, max_retries=3)
def process_transfer(self, sender_id, receiver_id, amount, txn_id):

    txn = Transaction.objects.get(id=txn_id)

    try:
        transfer_funds(
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=Decimal(amount),
            txn=txn   #  pass txn object
        )

        txn.status = Transaction.Status.SUCCESS
        txn.save(update_fields=["status"])

        return "success"

    except InsufficientFundsError:
        txn.status = Transaction.Status.FAILED
        txn.save(update_fields=["status"])
        return "failed_insufficient_funds"

    except IntegrityError as exc:
        raise self.retry(exc=exc)

    except Exception:
        txn.status = Transaction.Status.FAILED
        txn.save(update_fields=["status"])
        raise
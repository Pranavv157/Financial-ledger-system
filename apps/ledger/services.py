from django.db import transaction, IntegrityError
from decimal import Decimal

from .models import LedgerAccount, Transaction, TransactionEntry
from .selectors import get_account_balance
from .validators import validate_transaction_balance


def transfer_funds(sender_id, receiver_id, amount, reference_id):

    amount = Decimal(amount)

    if amount <= 0:
        raise ValueError("Amount must be positive")

    if sender_id == receiver_id:
        raise ValueError("Sender and receiver cannot be the same")

    # idempotency check
    existing = Transaction.objects.filter(reference_id=reference_id).first()
    if existing:
        return existing

    with transaction.atomic():

        # lock accounts in consistent order
        account_ids = sorted([sender_id, receiver_id])

        accounts = (
            LedgerAccount.objects
            .select_for_update()
            .filter(id__in=account_ids)
            .order_by("id")
        )

        accounts_map = {a.id: a for a in accounts}

        if len(accounts_map) != 2:
            raise ValueError("Invalid accounts")

        sender = accounts_map[sender_id]
        receiver = accounts_map[receiver_id]

        # check sender balance
        balance = get_account_balance(sender)

        if balance < amount:
            raise ValueError("Insufficient funds")

        try:
            txn = Transaction.objects.create(
                reference_id=reference_id,
                status=Transaction.Status.PENDING
            )

        except IntegrityError:
            return Transaction.objects.get(reference_id=reference_id)

        # prepare ledger entries
        entries = [
            {
                "account": sender,
                "type": TransactionEntry.DEBIT,
                "amount": amount
            },
            {
                "account": receiver,
                "type": TransactionEntry.CREDIT,
                "amount": amount
            },
        ]

        # validate double entry rule
        validate_transaction_balance(entries)

        # create entries
        for entry in entries:
            TransactionEntry.objects.create(
                transaction=txn,
                account=entry["account"],
                entry_type=entry["type"],
                amount=entry["amount"]
            )

        txn.status = Transaction.Status.SUCCESS
        txn.save(update_fields=["status"])

        return txn
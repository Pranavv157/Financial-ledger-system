from django.db import transaction, IntegrityError
from decimal import Decimal

from .models import LedgerAccount, Transaction, TransactionEntry
from .ledger_selectors import get_account_balance
from .validators import validate_transaction_balance
from .exceptions import InsufficientFundsError, InvalidTransferError


def transfer_funds(sender_id, receiver_id, amount, reference_id):

    amount = Decimal(amount)

    if amount <= 0:
        raise InvalidTransferError("Amount must be positive")

    if sender_id == receiver_id:
        raise InvalidTransferError("Sender and receiver cannot be the same")

    # idempotency check
    existing = Transaction.objects.filter(reference_id=reference_id).first()
    if existing:
        return existing

    with transaction.atomic():

        account_ids = sorted([sender_id, receiver_id])

        accounts = (
            LedgerAccount.objects
            .select_for_update()
            .filter(id__in=account_ids)
            .order_by("id")
        )

        accounts_map = {a.id: a for a in accounts}

        if len(accounts_map) != 2:
            raise InvalidTransferError("Invalid accounts")

        sender = accounts_map[sender_id]
        receiver = accounts_map[receiver_id]

        # balance check
        balance = get_account_balance(sender)

        if balance < amount:
            raise InsufficientFundsError("Insufficient funds")

        try:
            txn = Transaction.objects.create(
                reference_id=reference_id,
                status=Transaction.Status.PENDING
            )
        except IntegrityError:
            return Transaction.objects.get(reference_id=reference_id)

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

        validate_transaction_balance(entries)

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
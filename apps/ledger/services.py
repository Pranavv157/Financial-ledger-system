from django.db import transaction, IntegrityError
from decimal import Decimal
import uuid

from .ledger_selectors import get_account_balance
from .models import LedgerAccount, Transaction, TransactionEntry
from .validators import validate_transaction_balance
from .exceptions import InsufficientFundsError, InvalidTransferError


def transfer_funds(sender_id, receiver_id, amount, reference_id):

    amount = Decimal(amount)

    if amount <= 0:
        raise InvalidTransferError("Amount must be positive")

    if sender_id == receiver_id:
        raise InvalidTransferError("Sender and receiver cannot be the same")

    try:
        reference_id = uuid.UUID(str(reference_id))
    except ValueError:
        raise InvalidTransferError("Invalid reference_id format")

    with transaction.atomic():

        #  Idempotency
        existing = Transaction.objects.filter(reference_id=reference_id).first()
        if existing:
            return existing

        #  Lock accounts (avoid race conditions)
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

        #  STEP 1: Bootstrap ledger if missing
        sender_entries_exist = TransactionEntry.objects.filter(account=sender).exists()

        if not sender_entries_exist and sender.balance > 0:
            bootstrap_txn = Transaction.objects.create(
                reference_id=uuid.uuid4(),
                status=Transaction.Status.SUCCESS
            )

            TransactionEntry.objects.create(
                transaction=bootstrap_txn,
                account=sender,
                entry_type=TransactionEntry.CREDIT,
                amount=sender.balance
            )

        #  STEP 2: Use ledger as source of truth
        effective_balance = get_account_balance(sender)

        if effective_balance < amount:
            raise InsufficientFundsError("Insufficient funds")

        if receiver.balance + amount > 1000000:
            raise InvalidTransferError("Receiver account balance limit exceeded")

        #  Create transaction safely
        try:
            txn = Transaction.objects.create(
                reference_id=reference_id,
                status=Transaction.Status.PENDING
            )
        except IntegrityError:
            return Transaction.objects.get(reference_id=reference_id)

        # Double-entry
        entries = [
            {"account": sender, "type": TransactionEntry.DEBIT, "amount": amount},
            {"account": receiver, "type": TransactionEntry.CREDIT, "amount": amount},
        ]

        validate_transaction_balance(entries)

        for entry in entries:
            TransactionEntry.objects.create(
                transaction=txn,
                account=entry["account"],
                entry_type=entry["type"],
                amount=entry["amount"]
            )

        #  Update cached balances (mirror ledger)
        sender.balance -= amount
        receiver.balance += amount

        sender.save(update_fields=["balance"])
        receiver.save(update_fields=["balance"])

        txn.status = Transaction.Status.SUCCESS
        txn.save(update_fields=["status"])

        return txn


def reverse_transaction(transaction_id):

    with transaction.atomic():

        try:
            original_txn = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            raise ValueError("Transaction not found")

        if original_txn.status == Transaction.Status.REVERSED:
            raise ValueError("Transaction already reversed")

        reversal_txn = Transaction.objects.create(
            status=Transaction.Status.PENDING,
            reverses=original_txn
        )

        entries = TransactionEntry.objects.filter(transaction=original_txn)

        for entry in entries:
            reversed_type = (
                TransactionEntry.CREDIT
                if entry.entry_type == TransactionEntry.DEBIT
                else TransactionEntry.DEBIT
            )

            TransactionEntry.objects.create(
                transaction=reversal_txn,
                account=entry.account,
                entry_type=reversed_type,
                amount=entry.amount
            )

            #  Update balance correctly
            if reversed_type == TransactionEntry.CREDIT:
                entry.account.balance += entry.amount
            else:
                entry.account.balance -= entry.amount

            entry.account.save(update_fields=["balance"])

        reversal_txn.status = Transaction.Status.SUCCESS
        original_txn.status = Transaction.Status.REVERSED

        reversal_txn.save(update_fields=["status"])
        original_txn.save(update_fields=["status"])

        return reversal_txn
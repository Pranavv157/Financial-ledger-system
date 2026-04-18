import decimal
import platform
from django.db import transaction, IntegrityError
from decimal import Decimal
import uuid

from .ledger_selectors import get_account_balance
from .models import LedgerAccount, Transaction, TransactionEntry
from .validators import validate_transaction_balance
from .exceptions import InsufficientFundsError, InvalidTransferError


from django.db import transaction, IntegrityError
from decimal import Decimal
import uuid

from .ledger_selectors import get_account_balance
from .models import LedgerAccount, Transaction, TransactionEntry
from .validators import validate_transaction_balance
from .exceptions import InsufficientFundsError, InvalidTransferError

from django.contrib.auth import get_user_model

from .audit import log_action

User = get_user_model()

def get_platform_account():
    # get or create a system user
    platform_user, _ = User.objects.get_or_create(
        username="platform_system"
    )

    # create account linked to user
    account, _ = LedgerAccount.objects.get_or_create(
        user=platform_user,
        defaults={"balance": Decimal("0")}
    )

    return account

def transfer_funds(sender_id, receiver_id, amount, reference_id):
    
    reference_id = str(reference_id)

    #  robust fee detection
    fee = Decimal("5") if Decimal(amount) >= Decimal("100") else Decimal("0")
    amount=Decimal(amount)
    total_amount = amount + fee

    if total_amount <= 0:
        raise InvalidTransferError("Amount must be positive")

    if sender_id == receiver_id:
        raise InvalidTransferError("Sender and receiver cannot be the same")

    # Relaxed reference_id (supports strings like "ref-fee")
    reference_id = str(reference_id)

    with transaction.atomic():

        # Idempotency
        existing = Transaction.objects.filter(reference_id=reference_id).first()
        if existing:
            return existing

        # Lock accounts
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

        #  get platform account
        platform_account = get_platform_account()

        # Bootstrap ledger if needed
        sender_entries_exist = TransactionEntry.objects.filter(account=sender).exists()

        if not sender_entries_exist and sender.balance > 0:
            bootstrap_txn = Transaction.objects.create(
                reference_id=str(uuid.uuid4()),
                status=Transaction.Status.SUCCESS
            )

            TransactionEntry.objects.create(
                transaction=bootstrap_txn,
                account=sender,
                entry_type=TransactionEntry.CREDIT,
                amount=sender.balance
            )

        # Ledger balance
        effective_balance = get_account_balance(sender)

        if effective_balance < total_amount:
            raise InsufficientFundsError("Insufficient funds")

        if receiver.balance + amount > 1000000:
            raise InvalidTransferError("Receiver account balance limit exceeded")

        # Create transaction
        try:
            txn = Transaction.objects.create(
                reference_id=reference_id,
                status=Transaction.Status.PENDING
            )
        except IntegrityError:
            return Transaction.objects.get(reference_id=reference_id)

        #  Correct double-entry
        entries = [
            {
                "account": sender,
                "type": TransactionEntry.DEBIT,
                "amount": total_amount
            },
            {
                "account": receiver,
                "type": TransactionEntry.CREDIT,
                "amount": amount
            },
            {
                "account": platform_account,
                "type": TransactionEntry.CREDIT,
                "amount": fee
            }
        ]

        validate_transaction_balance(entries)

        for entry in entries:
            TransactionEntry.objects.create(
                transaction=txn,
                account=entry["account"],
                entry_type=entry["type"],
                amount=entry["amount"]
            )

        #  Correct balance updates
        sender.balance -= total_amount
        receiver.balance += amount
        platform_account.balance += fee

        sender.save(update_fields=["balance"]) 
        receiver.save(update_fields=["balance"])
        platform_account.save(update_fields=["balance"])

        txn.status = Transaction.Status.SUCCESS
        txn.save(update_fields=["status"])
       
        
    log_action(
    action="TRANSFER",
    user_id=sender.user_id,
    reference_id=str(reference_id),
    metadata={
        "sender": sender.id,
            "receiver": receiver.id,
            "amount": str(amount),
            "fee" : str(fee)
        }
    )

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

        
    log_action(
        action="REVERSAL",
        user_id=None,
        reference_id=str(original_txn.reference_id),
        metadata={
            "original_txn": original_txn.id,
            "reversal_txn": reversal_txn.id
            }
        )
    return reversal_txn
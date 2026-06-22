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

    amount = Decimal(amount)
    reference_id = str(reference_id)

    fee = Decimal("5") if amount >= Decimal("100") else Decimal("0")
    total_amount = amount + fee

    if total_amount <= 0:
        raise InvalidTransferError("Amount must be positive")

    if sender_id == receiver_id:
        raise InvalidTransferError("Sender and receiver cannot be same")

    #  STEP 1: PRE-CHECK IDEMPOTENCY (FAST PATH)
    try:
        txn=Transaction.Objects.create(
        reference_id=reference_id,
        status=Transaction.Status.PROCESSING
        )
    except IntegrityError:
        return Transaction.objects.get(
        reference_id=reference_id
        )

    if existing:

        if existing.status == Transaction.Status.PROCESSING:
            # another worker is already working
            return existing

    try:
        with transaction.atomic():

            txn = Transaction.objects.create(
                reference_id=reference_id,
                status=Transaction.Status.PROCESSING
            )

            #  LOCK ACCOUNTS
            account_ids = sorted([sender_id, receiver_id])
            accounts = (
                LedgerAccount.objects
                .select_for_update()
                .filter(id__in=account_ids)
            )

            if len(accounts) != 2:
                raise InvalidTransferError("Invalid accounts")

            acc_map = {a.id: a for a in accounts}
            sender = acc_map[sender_id]
            receiver = acc_map[receiver_id]

            #  BALANCE CHECK
            effective_balance = get_account_balance(sender)

            if effective_balance < total_amount:
                raise InsufficientFundsError("Insufficient funds")

            #  ENTRIES
            entries = [
                {"account": sender, "type": TransactionEntry.DEBIT, "amount": total_amount},
                {"account": receiver, "type": TransactionEntry.CREDIT, "amount": amount},
            ]

            if fee > 0:
                platform_account = get_platform_account()
                entries.append({
                    "account": platform_account,
                    "type": TransactionEntry.CREDIT,
                    "amount": fee
                })

            validate_transaction_balance(entries)

            for e in entries:
                TransactionEntry.objects.create(
                    transaction=txn,
                    account=e["account"],
                    entry_type=e["type"],
                    amount=e["amount"]
                )

            #  UPDATE BALANCES
            sender.balance -= total_amount
            receiver.balance += amount
            sender.save(update_fields=["balance"])
            receiver.save(update_fields=["balance"])

            if fee > 0:
                platform_account.balance += fee
                platform_account.save(update_fields=["balance"])

            txn.status = Transaction.Status.SUCCESS
            txn.save(update_fields=["status"])

        #  OUTSIDE TRANSACTION → SAFE
        log_action(
            action="TRANSFER",
            user_id=sender.user_id,
            reference_id=reference_id,
            metadata={
                "sender": sender.id,
                "receiver": receiver.id,
                "amount": str(amount),
                "fee": str(fee)
            }
        )

        return txn

    except Exception:

        # VERY IMPORTANT
        Transaction.objects.filter(reference_id=reference_id).update(
            status=Transaction.Status.FAILED
        )

        raise

def reverse_transaction(transaction_id):

    with transaction.atomic():

        try:
            original_txn = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            raise ValueError("Transaction not found")

        if original_txn.status == Transaction.Status.REVERSED:
            raise ValueError("Transaction already reversed")

        reversal_txn = Transaction.objects.create(
            status=Transaction.Status.PROCESSING,
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

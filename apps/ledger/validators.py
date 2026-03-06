from .models import TransactionEntry


def validate_transaction_balance(entries):

    #total debit must be equal to total credit
    total_debit = sum(
        e["amount"] for e in entries if e["type"] == TransactionEntry.DEBIT
    )

    total_credit = sum(
        e["amount"] for e in entries if e["type"] == TransactionEntry.CREDIT
    )

    if total_debit != total_credit:
        raise ValueError("Transaction entries are not balanced")
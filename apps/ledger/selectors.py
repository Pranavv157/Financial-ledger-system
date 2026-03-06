from django.db.models import Sum, Case, When, DecimalField
from django.db.models.functions import Coalesce
from .models import TransactionEntry


def get_account_balance(account):

    balance = (
        TransactionEntry.objects
        .filter(account=account)
        .aggregate(
            balance=Coalesce(
                Sum(
                    Case(
                        When(entry_type="CREDIT", then="amount"),
                        When(entry_type="DEBIT", then=-1 * "amount"),
                        output_field=DecimalField()
                    )
                ),
                0
            )
        )["balance"]
    )

    return balance
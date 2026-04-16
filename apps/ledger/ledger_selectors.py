from django.db.models import Sum, Case, When, DecimalField, F
from django.db.models.functions import Coalesce
from decimal import Decimal
from .models import TransactionEntry

def get_account_balance(account):
    return (
        TransactionEntry.objects
        .filter(account=account)
        .aggregate(
            balance=Coalesce(
                Sum(
                    Case(
                        When(entry_type=TransactionEntry.CREDIT, then=F("amount")),
                        When(entry_type=TransactionEntry.DEBIT, then=-F("amount")),
                        output_field=DecimalField()
                    )
                ),
                Decimal("0")
            )
        )["balance"]
    )
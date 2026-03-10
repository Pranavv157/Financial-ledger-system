from django.db.models import Sum, Case, When, F, DecimalField, Value
from django.db.models.functions import Coalesce
from .models import TransactionEntry


def get_account_balance(account):

    result = (
        TransactionEntry.objects
        .filter(account=account)
        .aggregate(
            balance=Coalesce(
                Sum(
                    Case(
                        When(
                            entry_type=TransactionEntry.CREDIT,
                            then=F("amount")
                        ),
                        When(
                            entry_type=TransactionEntry.DEBIT,
                            then=F("amount") * -1
                        ),
                        output_field=DecimalField(),
                    )
                ),
                Value(0, output_field=DecimalField()),
            )
        )
    )

    return result["balance"]
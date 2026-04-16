from django.db import models
from django.conf import settings
import uuid


class LedgerAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    balance = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=0
    )

    def __str__(self):
        return f"{self.name} - {self.user}"


import uuid
from django.db import models


class Transaction(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        REVERSED = "REVERSED", "Reversed"

    reference_id = models.UUIDField(unique=True, default=uuid.uuid4)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    reverses = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reversed_by"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.reverses and self.reverses == self:
            raise ValueError("Transaction cannot reverse itself")

        if self.reverses and self.reverses.reverses:
            raise ValueError("Cannot reverse a reversal")

    def __str__(self):
        return str(self.reference_id)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reverses"],
                name="unique_reversal_per_transaction"
            )
        ]
class TransactionEntry(models.Model):

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

    ENTRY_TYPES = [
        (DEBIT, "Debit"),
        (CREDIT, "Credit"),
    ]

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="entries"
    )

    account = models.ForeignKey(
        LedgerAccount,
        on_delete=models.CASCADE,
        related_name="entries"
    )

    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [
            models.Index(fields=["account", "created_at"]),
        ]
    
    def __str__(self):
        return f"{self.account} {self.entry_type} {self.amount}"
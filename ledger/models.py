from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid


class LedgerAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user}"


class Transaction(models.Model):
    reference_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference_id} - {self.status}"


class TransactionEntry(models.Model):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

    ENTRY_CHOICES = [
        (DEBIT, "Debit"),
        (CREDIT, "Credit")
    ]

    transaction = models.ForeignKey(
        Transaction,
        related_name="entries",
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(LedgerAccount, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=6, choices=ENTRY_CHOICES)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"{self.account} - {self.entry_type} - {self.amount}"
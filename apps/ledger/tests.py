from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
import uuid

from apps.ledger.models import LedgerAccount, TransactionEntry
from apps.ledger.services import transfer_funds

User = get_user_model()


class TransferTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")

        self.acc1 = LedgerAccount.objects.create(user=self.user1, name="pranav")
        self.acc2 = LedgerAccount.objects.create(user=self.user2, name="vaishnavi")

    def add_balance(self, account, amount):
        from apps.ledger.models import Transaction, TransactionEntry

        txn = Transaction.objects.create(reference_id=uuid.uuid4())

        TransactionEntry.objects.create(
            transaction=txn,
            account=account,
            entry_type=TransactionEntry.CREDIT,
            amount=amount
        )

    def test_successful_transfer(self):
        self.add_balance(self.acc1, Decimal("100"))

        txn = transfer_funds(
            sender_id=self.acc1.id,
            receiver_id=self.acc2.id,
            amount=Decimal("50"),
            reference_id=uuid.uuid4()   # FIX
        )

        self.assertEqual(txn.status, "SUCCESS")

        entries = TransactionEntry.objects.filter(transaction=txn)
        self.assertEqual(entries.count(), 2)

    def test_insufficient_funds(self):

        with self.assertRaises(Exception):
            transfer_funds(
                sender_id=self.acc1.id,
                receiver_id=self.acc2.id,
                amount=Decimal("100"),
                reference_id=uuid.uuid4()   #  FIX
            )

    def test_idempotency(self):
        self.add_balance(self.acc1, Decimal("100"))

        ref_id = uuid.uuid4()  #  SAME UUID for idempotency

        txn1 = transfer_funds(
            self.acc1.id,
            self.acc2.id,
            Decimal("10"),
            ref_id
        )

        txn2 = transfer_funds(
            self.acc1.id,
            self.acc2.id,
            Decimal("10"),
            ref_id
        )

        self.assertEqual(txn1.id, txn2.id)
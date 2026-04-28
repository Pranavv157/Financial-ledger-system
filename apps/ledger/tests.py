from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
import uuid
from unittest.mock import patch
from apps.ledger.models import Transaction
from apps.ledger.models import LedgerAccount, TransactionEntry
from apps.ledger.services import transfer_funds
from apps.ledger.ledger_selectors import get_account_balance
from apps.ledger.exceptions import InsufficientFundsError
from unittest.mock import patch
from .services import reverse_transaction
from .services import get_platform_account
from apps.ledger.reconciliation import reconcile_account

User = get_user_model()


class TransferTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")

        self.acc1 = LedgerAccount.objects.create(user=self.user1, name="pranav")
        self.acc2 = LedgerAccount.objects.create(user=self.user2, name="vaishnavi")
        self.platform_account = get_platform_account()

    def add_balance(self, account, amount):
        txn = Transaction.objects.create(reference_id=uuid.uuid4())

        TransactionEntry.objects.create(
            transaction=txn,
            account=account,
            entry_type=TransactionEntry.CREDIT,
            amount=amount
        )

        #keep balance in sync
        account.balance += amount
        account.save(update_fields=["balance"])
    def test_successful_transfer(self):
        self.add_balance(self.acc1, Decimal("100"))

        txn = transfer_funds(
            self.acc1.id,
            self.acc2.id,
            Decimal("50"),
            uuid.uuid4()
            )

        self.assertEqual(txn.status, "SUCCESS")
        self.assertEqual(TransactionEntry.objects.filter(transaction=txn).count(), 2)

    def test_insufficient_funds(self):
        with self.assertRaises(InsufficientFundsError):
            transfer_funds(
                self.acc1.id,
                self.acc2.id,
                Decimal("100"),
                uuid.uuid4()
            )

    def test_idempotency(self):
        self.add_balance(self.acc1, Decimal("100"))

        ref_id = uuid.uuid4()

        txn1 = transfer_funds(self.acc1.id, self.acc2.id, Decimal("10"), ref_id)
        txn2 = transfer_funds(self.acc1.id, self.acc2.id, Decimal("10"), ref_id)

        self.assertEqual(txn1.id, txn2.id)

    def test_balance_updates_after_transfer(self):
        self.acc1.balance = Decimal("100")
        self.acc1.save()

        transfer_funds(
            self.acc1.id,
            self.acc2.id,
            Decimal("40"),
            uuid.uuid4()
        )

        self.acc1.refresh_from_db()
        self.acc2.refresh_from_db()

        self.assertEqual(self.acc1.balance, Decimal("60"))
        self.assertEqual(self.acc2.balance, Decimal("40"))

    def test_balance_matches_ledger(self):
        self.acc1.balance = Decimal("100")
        self.acc1.save()

        transfer_funds(
            self.acc1.id,
            self.acc2.id,
            Decimal("30"),
            uuid.uuid4()
        )

        

        self.acc1.refresh_from_db()
        self.acc2.refresh_from_db()

        self.assertEqual(self.acc1.balance, get_account_balance(self.acc1))
        self.assertEqual(self.acc2.balance, get_account_balance(self.acc2))

    def test_insufficient_balance_with_cached_field(self):
        self.acc1.balance = Decimal("10")
        self.acc1.save()

        

        with self.assertRaises(InsufficientFundsError):
            transfer_funds(
                self.acc1.id,
                self.acc2.id,
                Decimal("50"),
                uuid.uuid4()
            )

    def test_atomicity_no_partial_update(self):
        self.acc1.balance = Decimal("100")
        self.acc1.save()

        

        with patch("apps.ledger.services.TransactionEntry.objects.create") as mock_create:
            mock_create.side_effect = Exception("DB failure")

            try:
                transfer_funds(
                    self.acc1.id,
                    self.acc2.id,
                    Decimal("50"),
                    uuid.uuid4()
                )
            except:
                pass

        self.acc1.refresh_from_db()
        self.acc2.refresh_from_db()

        self.assertEqual(self.acc1.balance, Decimal("100"))
        self.assertEqual(self.acc2.balance, Decimal("0"))

    def set_balance(self, account, amount):
        

        txn = Transaction.objects.create(reference_id=uuid.uuid4())

        TransactionEntry.objects.create(
            transaction=txn,
            account=account,
            entry_type=TransactionEntry.CREDIT,
            amount=amount
        )

        account.balance = amount
        account.save(update_fields=["balance"])

    def test_transaction_reversal(self):
        self.acc1.balance = Decimal("100")
        self.acc1.save()

        txn = transfer_funds(
            self.acc1.id,
            self.acc2.id,
            Decimal("50"),
            uuid.uuid4()
        )

        reverse_transaction(txn.id)

        self.acc1.refresh_from_db()
        self.acc2.refresh_from_db()

        self.assertEqual(self.acc1.balance, Decimal("100"))
        self.assertEqual(self.acc2.balance, Decimal("0"))

    def test_transfer_with_fee(self):
        self.acc1.balance = Decimal("200")
        self.acc1.save()

        txn = transfer_funds(
            self.acc1.id,
            self.acc2.id,
            Decimal("100"),
            uuid.uuid4()
        )

        self.acc1.refresh_from_db()
        self.acc2.refresh_from_db()
        self.platform_account.refresh_from_db()

        self.assertEqual(self.acc1.balance, Decimal("95"))   # 200 - 105
        self.assertEqual(self.acc2.balance, Decimal("100"))
        self.assertEqual(self.platform_account.balance, Decimal("5"))
    
    def test_reconciliation_fixes_balance(self):
        self.set_balance(self.acc1, Decimal("100"))

        # corrupt balance
        self.acc1.balance = Decimal("50")
        self.acc1.save()

        
        reconcile_account(self.acc1.id)

        self.acc1.refresh_from_db()

        self.assertEqual(
            self.acc1.balance,
            get_account_balance(self.acc1)
        )
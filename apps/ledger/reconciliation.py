import logging
from django.db import transaction

from .models import LedgerAccount
from .ledger_selectors import get_account_balance
from .audit import log_action


logger = logging.getLogger(__name__)


def reconcile_account(account_id):

    try:
        account = LedgerAccount.objects.get(id=account_id)
    except LedgerAccount.DoesNotExist:
        logger.warning(
            "reconciliation_account_not_found",
            extra={"account_id": account_id}
        )
        return

    # compute correct balance from ledger
    correct_balance = get_account_balance(account)

    # compare
    if account.balance != correct_balance:
        old_balance = account.balance

        with transaction.atomic():
            account.balance = correct_balance
            account.save(update_fields=["balance"])

        #  IMPORTANT LOG
        logger.error(
            "reconciliation_mismatch_fixed",
            extra={
                "account_id": account_id,
                "old_balance": str(old_balance),
                "correct_balance": str(correct_balance),
                "difference": str(correct_balance - old_balance),
            }
        )
        log_action(
            action="RECONCILIATION",
            reference_id=str(account_id),
            metadata={
                "old_balance": str(old_balance),
                "new_balance": str(correct_balance)
            }
        )

    else:
        # optional (can remove in production if too noisy)
        logger.info(
            "reconciliation_ok",
            extra={
                "account_id": account_id,
                "balance": str(account.balance),
            }
        )


def reconcile_all_accounts():

    logger.info("reconciliation_started")

    accounts = LedgerAccount.objects.all()

    for account in accounts:
        reconcile_account(account.id)

    logger.info("reconciliation_completed")
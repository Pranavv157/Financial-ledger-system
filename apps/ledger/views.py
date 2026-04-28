import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import transfer_funds
from .serializers import TransferSerializer, TransactionEntrySerializer
from .exceptions import InsufficientFundsError, InvalidTransferError
from .ledger_selectors import get_account_balance
from .models import LedgerAccount, TransactionEntry ,Transaction , AuditLog
from .pagination import TransactionPagination
from .tasks import process_transfer


logger = logging.getLogger(__name__)


class TransferAPIView(APIView):

    def post(self, request):

        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            process_transfer.delay(
                sender_id=data["sender_id"],
                receiver_id=data["receiver_id"],
                amount=str(data["amount"]),
                reference_id=str(data["reference_id"]),
            )

            logger.info(
                "transfer_queued",
                extra={
                    "sender_id": data["sender_id"],
                    "receiver_id": data["receiver_id"],
                    "amount": str(data["amount"]),
                    "reference_id": str(data["reference_id"]),
                }
            )

            return Response(
                {
                    "status": "processing",
                    "reference_id": str(data["reference_id"])
                },
                status=status.HTTP_202_ACCEPTED
            )

        except Exception:

            logger.exception("transfer_queue_failed")

            return Response(
                {"error": "Failed to queue transfer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class AccountTransactionsAPIView(APIView):

    def get(self, request, account_id):

        entries = (
            TransactionEntry.objects
            .filter(account_id=account_id)
            .order_by("-created_at")
        )

        paginator = TransactionPagination()
        paginated_entries = paginator.paginate_queryset(entries, request)

        serializer = TransactionEntrySerializer(paginated_entries, many=True)

        return paginator.get_paginated_response(serializer.data)


class TransferStatusAPIView(APIView):

    def get(self, request, reference_id):

        try:
            txn = Transaction.objects.get(reference_id=reference_id)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "reference_id": str(txn.reference_id),
            "status": txn.status,
            "created_at": txn.created_at.isoformat(),
            "updated_at": txn.updated_at.isoformat(),
        })


class AccountBalanceAPIView(APIView):

    def get(self, request, account_id):

        try:
            account = LedgerAccount.objects.get(id=account_id)
        except LedgerAccount.DoesNotExist:
            return Response(
                {"error": "Account not found"},
                status=status.HTTP_404_NOT_FOUND
            )
       
        return Response(
            {
                "account_id": account.id,
                "balance": account.balance
            },
            status=status.HTTP_200_OK
        )
        logger.info(
                "balance_fetched",
                extra={
                    "account_id": account.id,
                    "balance": str(account.balance)
                }
            )
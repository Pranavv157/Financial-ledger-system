import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import transfer_funds
from .serializers import (
TransferSerializer,
TransactionEntrySerializer,
)
from .exceptions import (
InsufficientFundsError,
InvalidTransferError,
)
from .models import (
LedgerAccount,
TransactionEntry,
Transaction,
)

from .pagination import TransactionPagination

logger = logging.getLogger(__name__)

class TransferAPIView(APIView):

    def post(self, request):

        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:

            txn = transfer_funds(
                sender_id=data["sender_id"],
                receiver_id=data["receiver_id"],
                amount=str(data["amount"]),
                reference_id=str(data["reference_id"]),
            )

            logger.info(
                "transfer_completed",
                extra={
                    "transaction_id": txn.id,
                    "reference_id": str(txn.reference_id),
                    "sender_id": data["sender_id"],
                    "receiver_id": data["receiver_id"],
                    "amount": str(data["amount"]),
                }
            )

            return Response(
                {
                    "transaction_id": txn.id,
                    "reference_id": str(txn.reference_id),
                    "status": txn.status,
                },
                status=status.HTTP_200_OK
            )

        except (
            InsufficientFundsError,
            InvalidTransferError
        ) as e:

            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:

            logger.exception(
                "transfer_failed"
            )

            return Response(
                {"error": "Transfer failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

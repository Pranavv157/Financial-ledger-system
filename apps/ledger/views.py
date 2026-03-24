import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import transfer_funds
from .serializers import TransferSerializer, TransactionEntrySerializer
from .exceptions import InsufficientFundsError, InvalidTransferError
from .ledger_selectors import get_account_balance
from .models import LedgerAccount, TransactionEntry
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
                amount=data["amount"],
                reference_id=data["reference_id"],
            )

            #  SUCCESS LOG
            logger.info(
                "transfer_success",
                extra={
                    "sender_id": data["sender_id"],
                    "receiver_id": data["receiver_id"],
                    "amount": str(data["amount"]),
                    "reference_id": str(data["reference_id"]),
                    "transaction_id": txn.id,
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

        except InsufficientFundsError as e:

            #  BUSINESS FAILURE LOG
            logger.warning(
                "transfer_failed_insufficient_funds",
                extra={
                    "sender_id": data["sender_id"],
                    "receiver_id": data["receiver_id"],
                    "amount": str(data["amount"]),
                    "reference_id": str(data["reference_id"]),
                    "error": str(e),
                }
            )

            return Response(
                {
                    "error": {
                        "code": "insufficient_funds",
                        "message": str(e),
                    }
                },
                status=status.HTTP_409_CONFLICT
            )

        except InvalidTransferError as e:

            logger.warning(
                "transfer_failed_invalid",
                extra={
                    "sender_id": data["sender_id"],
                    "receiver_id": data["receiver_id"],
                    "amount": str(data["amount"]),
                    "reference_id": str(data["reference_id"]),
                    "error": str(e),
                }
            )

            return Response(
                {
                    "error": {
                        "code": "invalid_transfer",
                        "message": str(e)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:

            #  SYSTEM ERROR LOG (VERY IMPORTANT)
            logger.exception(
                "transfer_unexpected_error",
                extra={
                    "sender_id": data.get("sender_id"),
                    "receiver_id": data.get("receiver_id"),
                    "amount": str(data.get("amount")),
                    "reference_id": str(data.get("reference_id")),
                }
            )

            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AccountBalanceAPIView(APIView):

    def get(self, request, account_id):

        try:
            account = LedgerAccount.objects.get(id=account_id)
        except LedgerAccount.DoesNotExist:
            return Response(
                {"error": "Account not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        balance = get_account_balance(account)

        return Response({
            "account_id": account_id,
            "balance": balance
        }, status=status.HTTP_200_OK)
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

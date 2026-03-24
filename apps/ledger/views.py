import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import transfer_funds
from .serializers import TransferSerializer, TransactionEntrySerializer
from .exceptions import InsufficientFundsError, InvalidTransferError
from .ledger_selectors import get_account_balance
from .models import LedgerAccount, TransactionEntry


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

            return Response(
                {
                    "transaction_id": txn.id,
                    "reference_id": str(txn.reference_id),
                    "status": txn.status,
                },
                status=status.HTTP_200_OK
            )

        except InsufficientFundsError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_409_CONFLICT
            )

        except InvalidTransferError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.exception("Unexpected transfer error")
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
        })


class AccountTransactionsAPIView(APIView):

    def get(self, request, account_id):

        entries = (
            TransactionEntry.objects
            .filter(account_id=account_id)
            .order_by("-created_at")
        )

        serializer = TransactionEntrySerializer(entries, many=True)

        return Response(serializer.data)
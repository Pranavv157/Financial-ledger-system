from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import transfer_funds
from .serializers import TransferSerializer


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
                    "status": "success",
                }
            )

        except ValueError as e:
            print("TRANSFER ERROR:", str(e))

            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
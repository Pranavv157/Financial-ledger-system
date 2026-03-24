from rest_framework import serializers
import uuid
from .models import TransactionEntry


class TransferSerializer(serializers.Serializer):
    sender_id = serializers.IntegerField()
    receiver_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    reference_id = serializers.UUIDField(required=False)

    def validate(self, data):
        if data["sender_id"] == data["receiver_id"]:
            raise serializers.ValidationError("Sender and receiver cannot be the same")

        if data["amount"] <= 0:
            raise serializers.ValidationError("Amount must be positive")

        if "reference_id" not in data:
            data["reference_id"] = uuid.uuid4()

        return data


class TransactionEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = TransactionEntry
        fields = [
            "transaction",
            "entry_type",
            "amount",
            "created_at"
        ]
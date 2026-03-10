from rest_framework import serializers
from .models import TransactionEntry



class TransferSerializer(serializers.Serializer):
    sender_id = serializers.IntegerField()
    receiver_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    reference_id = serializers.UUIDField()



class TransactionEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = TransactionEntry
        fields = [
            "transaction",
            "entry_type",
            "amount",
            "created_at"
        ]
from rest_framework import serializers

from api.models import Item, Transaction


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'amount', 'created_at', 'updated_at', 'state']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'item', 'status', 'location', 'is_active', 'created_at', 'updated_at']

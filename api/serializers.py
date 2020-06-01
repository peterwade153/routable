from rest_framework import serializers

from api.models import Item, Transaction


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        read_only_fields = ['id' , 'created_at', 'updated_at', 'state']
        fields = read_only_fields + ['amount']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']
        fields = read_only_fields + ['item', 'status', 'location']

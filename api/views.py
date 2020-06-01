from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from api.models import Item, Transaction
from api.serializers import ItemSerializer, TransactionSerializer


class ItemCreateView(APIView):
    """
    Creates a new item.
    params :
        - amount
    """

    @swagger_auto_schema(request_body=ItemSerializer,operation_description="Create transaction item")
    def post(self, request):
        serializer = ItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionCreateView(APIView):
    """
    Creates a new Item transaction, if it has no existing active transaction.
    For proper flow. status and location should the values indicated below.
    params :
        - item
        - status = processing
        - location = origination_bank
    """
    @swagger_auto_schema(request_body=TransactionSerializer, operation_description='Create Item Transaction')
    def post(self, request):
        data = request.data
        item_pk = data.get('item', None)
        status_ = data.get('status', None)
        location = data.get('location', None)

        try:
            item_obj = Item.objects.get(id=item_pk)
        except Item.DoesNotExist:
            return Response('Item doesnt exist', status=status.HTTP_400_BAD_REQUEST)

        transactions = Transaction.objects.filter(item__pk=item_pk)
        if transactions.filter(is_active=True):
            return Response(
                'There is an active transaction for this item', 
                status=status.HTTP_400_BAD_REQUEST
            )
        elif transactions.filter(status=Transaction.COMPLETED):
            return Response(
                'Item transaction completed', 
                status=status.HTTP_400_BAD_REQUEST
            )
        elif transactions.filter(status=Transaction.REFUNDED):
            return Response(
                'Item transaction refunded', 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure for each new transaction status = processing and location = origin on creation
        if status_ != Transaction.PROCESSING or location != Transaction.ORIGIN:
            return Response('Transactions should have status = processing'+
                ' and location = origination_bank',
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class MoveItemView(APIView):
    """
    Moves an Item’s active Transaction status and location to next possible states 
    """
    def put(self, request, pk):

        try:
            trans_obj = Transaction.objects.get(
                item__pk=pk, 
                is_active=True
            )
        except Transaction.DoesNotExist:
            return Response(
                'Item has no active transaction or Item doesnt exist', 
                status=status.HTTP_400_BAD_REQUEST
            )

        if trans_obj.status == Transaction.ERROR:
            return Response(
                'Transaction errored, can not be moved', 
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status, new_location = trans_obj.get_new_transaction_state()
        # update transaction status and location
        trans_obj.move_transaction(new_status, new_location)

        # update item state
        item_obj = Item.objects.get(pk=pk)
        item_obj.update_item_state(trans_obj.status)

        return Response("Item moved", status=status.HTTP_200_OK)


class ErrorItemView(APIView):
    """
    Marks an Item’s active Transaction status from processing to error
    """
    def put(self, request, pk):
        try:
            trans_obj = Transaction.objects.get(
                item__pk=pk, 
                is_active=True, 
                location=Transaction.ROUTABLE,
                status=Transaction.PROCESSING
            )
        except Transaction.DoesNotExist:
            return Response(
                'Action failed',
                status=status.HTTP_400_BAD_REQUEST
            )
        if trans_obj.status == Transaction.ERROR:
            return Response(
                'Item transaction already errored', 
                status=status.HTTP_400_BAD_REQUEST
            )
        # update item transaction state to error
        trans_obj.error_transaction()

        # update item state
        item_obj = Item.objects.get(pk=pk)
        item_obj.update_item_state(trans_obj.status)

        return Response(
            "Item status changed to error", 
            status=status.HTTP_200_OK
        )


class FixItemView(APIView):
    """
    Fixes the transaction in error state, creates new transaction with status fixing.
    """
    def put(self, request, pk):
        try:
            trans_obj = Transaction.objects.get(
                item__pk=pk, 
                is_active=True,
                status=Transaction.ERROR
            )
        except Transaction.DoesNotExist:
            return Response(
                'Action failed', 
                status=status.HTTP_400_BAD_REQUEST
            )
        # deactivate current active transaction in error state.
        trans_obj.deactivate_transaction()

        # Create a new transaction
        trans_obj = Transaction.objects.create(
            item_id=pk, 
            status="fixing",
            location="routable"
        )
        # update item state
        item_obj = Item.objects.get(pk=pk)
        item_obj.update_item_state(trans_obj.status)

        return Response("Fixing Item transaction", status=status.HTTP_200_OK)

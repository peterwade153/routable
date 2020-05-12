from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from api.models import Item, Transaction
from api.serializers import ItemSerializer, TransactionSerializer


class ItemCreateView(APIView):
    """
    Creates a new item.
    params :
        - amount
    """
    def post(self, request):
        serializer = ItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionCreateView(APIView):
    """
    Creates a new transaction for an Item, if it has no existing active transaction.
    For proper flow. status and location should the values indicated below.
    params :
        - item
        - status = processing
        - location = origination_bank
    """
    def post(self, request):
        data = request.data
        item_pk = data.get('item', None)
        status_ = data.get('status', Transaction.PROCESSING)
        location = data.get('location', Transaction.ORIGIN)

        try:
            item_obj = Item.objects.get(id=item_pk)
        except Item.DoesNotExist:
            return Response('Item doesnt exist', status=status.HTTP_400_BAD_REQUEST)


        transactions = Transaction.objects.filter(item=item_obj)

        # Item has completed and inactive transactions
        if transactions.filter(status=Transaction.COMPLETED):
            return Response(
                "Item is transaction completed", 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Active transactions
        active_trans = transactions.filter(is_active=True)
        errored_active_trans = active_trans.filter(status=Transaction.ERROR).first()
        if errored_active_trans:
            errored_active_trans.is_active = False
            errored_active_trans.save()

            Transaction.objects.create(
                item_id=item_pk,
                status=Transaction.PROCESSING,
                location=Transaction.ORIGIN
            )
            return Response("New Transaction created", status=status.HTTP_201_CREATED)

        elif active_trans.filter(status=Transaction.PROCESSING).first():
            return Response("Item Transaction processing", status.HTTP_400_BAD_REQUEST)
        
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
    params :
        - item
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
        trans_obj.status = new_status
        trans_obj.location = new_location
        trans_obj.save()

        # update item state
        item_obj = Item.objects.get(pk=pk)
        new_state = item_obj.get_new_item_state(trans_obj.status)
        item_obj.state = new_state
        item_obj.save()

        return Response("Item moved", status=status.HTTP_200_OK)


class ErrorItemView(APIView):
    """
    Marks an Item’s active Transaction status to error
    params :
        - item
    """

    def put(self, request, pk):
        # For proper flow, transaction location = routable, to error transaction
        try:
            trans_obj = Transaction.objects.get(
                item__pk=pk, 
                is_active=True, 
                location=Transaction.ROUTABLE)
        except Transaction.DoesNotExist:
            return Response('Item has no active transaction or ' 
                +'transaction location is not routable or Item doesnt exist',
                status=status.HTTP_400_BAD_REQUEST
            )
        if trans_obj.status == Transaction.ERROR:
            return Response(
                'Item transaction already errored', 
                status=status.HTTP_400_BAD_REQUEST
            )
        # change item transaction state to error
        trans_obj.status = Transaction.ERROR
        trans_obj.save()

        # update item state
        item_obj = Item.objects.get(pk=pk)
        new_state = item_obj.get_new_item_state(trans_obj.status)
        item_obj.state = new_state
        item_obj.save()

        return Response(
            "Item status changed to error", 
            status=status.HTTP_200_OK
        )

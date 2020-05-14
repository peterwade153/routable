from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.views import status

from api.models import Item, Transaction

import json

class RoutableAPITestCase(APITestCase):

    def setUp(self):
        self.item_1 = Item.objects.create(amount=1234)
        self.item_2 = Item.objects.create(amount=1000)
        self.item_3 = Item.objects.create(amount=1000)
        self.transaction = Transaction.objects.create(
            item=self.item_2, 
            status="processing",
            location="origination_bank"
        )


    def test_create_item(self):
        data = {"amount": 123}
        res = self.client.post('/api/items', data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_item_with_invalid_data(self):
        data = {"amount": " "}
        res = self.client.post('/api/items', data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

#Transaction tests

    def test_create_item_transaction(self):
        data = {
            "item": self.item_1.id, 
            "status":"processing", 
            "location":"origination_bank"
        }
        res = self.client.post('/api/items/transaction', data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_transaction_for_nonexistant_item(self):
        item_id = "d0ef03f4-e2e9-4830-98bd-2df78db5da65"
        data = {
            "item": item_id, 
            "status":"processing", 
            "location":"origination_bank"
        }
        res = self.client.post('/api/items/transaction', data)
        self.assertEqual(res.data, "Item doesnt exist")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_item_transaction_with_invalid_status_and_location(self):
        """
        A new transaction must have status = processing and 
        location = origination_bank.
        """
        data = {
            "item": self.item_1.id, 
            "status":"processing", 
            "location":"routable"
        }
        res = self.client.post('/api/items/transaction', data)
        self.assertEqual(
            res.data, 
            "Transactions should have status = processing and location = origination_bank"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_item_transaction_with_other_active_transactions(self):
        data = {
            "item": self.item_2.id, 
            "status":"processing", 
            "location":"origination_bank"
        }
        res = self.client.post('/api/items/transaction', data)
        self.assertEqual(res.data, "There is an active transaction for this item")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_item_transaction_with_completed_transactions(self):
        data = {
            "item": self.item_2.id, 
            "status":"processing", 
            "location":"origination_bank"
        }
        self.client.put(reverse('move_item', kwargs={'pk':self.item_2.id})) #moves item to routable
        self.client.put(reverse('move_item', kwargs={'pk':self.item_2.id})) #moves item to completed
        res = self.client.post('/api/items/transaction', data)
        self.assertEqual(res.data, "Item transaction completed")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_item_transaction_with_refunded_transaction(self):
        Transaction.objects.create(
            item_id=self.item_3.id, 
            status="refunded", 
            location="origination_bank"
        )
        data = {
            "item": self.item_3.id, 
            "status":"processing", 
            "location":"origination_bank"
        }
        res = self.client.post('/api/items/transaction', data)
        self.assertEqual(res.data, "Item transaction refunded")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

# Move Item Tests

    def test_move_item(self):
        item = Item.objects.create(amount=12345)
        Transaction.objects.create(
            item=item, 
            status="processing",
            location="origination_bank"
        )
        res = self.client.put(reverse('move_item', kwargs={'pk':item.id}))
        self.assertEqual(res.data, "Item moved")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_move_non_existant_item(self):
        item_id = "d0ef03f4-e2e9-4830-98bd-2df78db5da65"
        res = self.client.put(reverse('move_item', kwargs={'pk':item_id}))
        self.assertEqual(res.data, "Item has no active transaction or Item doesnt exist")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_move_completed_item_transaction(self):
        item = Item.objects.create(amount=12345)
        Transaction.objects.create(
            item=item, 
            status="processing",
            location="origination_bank"
        )
        self.client.put(reverse('move_item', kwargs={'pk':item.id})) # moves item to status processing and location routable
        self.client.put(reverse('move_item', kwargs={'pk':item.id})) # moves item to status completed and location destination bank
        res = self.client.put(reverse('move_item', kwargs={'pk':item.id}))
        self.assertEqual(res.data, "Item has no active transaction or Item doesnt exist")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_move_errored_item_transaction(self):
        item = Item.objects.create(amount=12345)
        Transaction.objects.create(
            item=item, 
            status="processing",
            location="origination_bank"
        )
        data = {"item": item.id}
        self.client.put(reverse('move_item', kwargs={'pk':item.id})) # moves item to status processing and location routable
        self.client.put(reverse('error_item', kwargs={'pk':item.id}))
        res = self.client.put(reverse('move_item', kwargs={'pk':item.id}))
        self.assertEqual(res.data, "Transaction errored, can not be moved")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

# Test Error Items
    def test_error_item(self):
        item = Item.objects.create(amount=12345)
        Transaction.objects.create(
            item=item, 
            status="processing",
            location="origination_bank"
        )
        self.client.put(reverse('move_item', kwargs={'pk':item.id})) # moves transaction location to routable
        res = self.client.put(reverse('error_item', kwargs={'pk':item.id}))
        self.assertEqual(res.data, 'Item status changed to error')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_error_non_existant_item(self):
        item_id = "d0ef03f4-e2e9-4830-98bd-2df78db5da65"
        res = self.client.put(reverse('error_item', kwargs={'pk':item_id}))
        self.assertEqual(
            res.data, 
            "Action failed"
            )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_error_completed_item_transaction(self):
        item = Item.objects.create(amount=12345)
        Transaction.objects.create(
            item=item, 
            status="processing",
            location="origination_bank"
        )
        self.client.put(reverse('move_item', kwargs={'pk':item.id})) # moves transaction location to routable
        self.client.put(reverse('move_item', kwargs={'pk':item.id})) # moves transaction location to destination bank
        res = self.client.put(reverse('error_item', kwargs={'pk':item.id}))
        self.assertEqual(
            res.data, 
            'Action failed'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_error_item_with_transaction_location_at_origination_bank(self):
        item = Item.objects.create(amount=12345)
        Transaction.objects.create(
            item=item, 
            status="processing",
            location="origination_bank"
        )
        res = self.client.put(reverse('error_item', kwargs={'pk':item.id}))
        self.assertEqual(
            res.data, 
            'Action failed'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_error_already_errored_item(self):
        item = Item.objects.create(amount=12345)
        Transaction.objects.create(
            item=item, 
            status="processing",
            location="origination_bank"
        )
        self.client.put(reverse('move_item', kwargs={'pk':item.id})) # moves transaction location to routable
        self.client.put(reverse('error_item', kwargs={'pk':item.id}))
        res = self.client.put(reverse('error_item', kwargs={'pk':item.id}))
        self.assertEqual(res.data, 'Action failed')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# test fixing transaction

    def test_fix_item_transaction(self):
        item = Item.objects.create(amount=12345)
        Transaction.objects.create(
            item=item, 
            status="processing",
            location="origination_bank"
        )
        self.client.put(reverse('move_item', kwargs={'pk':item.id})) # moves transaction location to routable
        self.client.put(reverse('error_item', kwargs={'pk':item.id})) #move transaction status to error
        res = self.client.put(reverse('fix_item', kwargs={'pk':item.id}))
        self.assertEqual(res.data, 'Fixing Item transaction')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_fix_non_existant_item(self):
        item_id = "d0ef03f4-e2e9-4830-98bd-2df78db5da65"
        res = self.client.put(reverse('fix_item', kwargs={'pk':item_id}))
        self.assertEqual(
            res.data,
            "Action failed"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fix_item_transaction_with_status_not_error(self):
        item = Item.objects.create(amount=12345)
        Transaction.objects.create(
            item=item, 
            status="processing",
            location="origination_bank"
        )
        self.client.put(reverse('move_item', kwargs={'pk':item.id})) # moves transaction location to routable
        res = self.client.put(reverse('fix_item', kwargs={'pk':item.id}))
        self.assertEqual(
            res.data, 
            'Action failed'
            )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
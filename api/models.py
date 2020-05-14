import uuid

from django.db import models


class Item(models.Model):

    PROCESSING, CORRECTING, ERROR, RESOLVED = ('processing', 'correcting', 'error', 'resolved')
    STATE_CHOICES = (
        (PROCESSING, 'Processing'),
        (CORRECTING, 'Correcting'),
        (ERROR, 'Error'),
        (RESOLVED, 'resolved')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    state = models.CharField(max_length=32, choices=STATE_CHOICES, default=PROCESSING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_new_item_state(self, trans_status):
        """
        Returns the next possible item state
        """
        if trans_status == Transaction.PROCESSING:
            return self.PROCESSING
        elif trans_status == Transaction.ERROR:
            return self.ERROR
        elif trans_status in [Transaction.COMPLETED, Transaction.REFUNDED]:
            return self.RESOLVED
        elif trans_status in [Transaction.REFUNDING, Transaction.FIXING]:
            return self.CORRECTING

    def update_item_state(self, trans_status):
        new_state = self.get_new_item_state(trans_status)
        self.state = new_state
        self.save()

    class Meta:
        ordering = ('-created_at', )


class Transaction(models.Model):

    PROCESSING = 'processing'
    COMPLETED = 'completed'
    ERROR = 'error'
    REFUNDING = 'refunding'
    REFUNDED = 'refunded'
    FIXING = 'fixing'

    STATUS_CHOICES = (
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (ERROR, 'Error'),
        (REFUNDING,'Refunding'),
        (REFUNDED, 'Refunded'),
        (FIXING, 'Fixing'),
    )

    ORIGIN, ROUTABLE, DESTINATION = ('origination_bank', 'routable', 'destination_bank')
    LOCATION_CHOICES = (
	    (ORIGIN, 'Origination Bank'),
	    (ROUTABLE, 'Routable'),
	    (DESTINATION, 'Destination Bank'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=PROCESSING)
    location = models.CharField(max_length=32, choices=LOCATION_CHOICES, default=ORIGIN)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        # Sets transaction to Inactive when its' status is completed
        if self.status in [self.COMPLETED, self.REFUNDED]:
            self.is_active = False
        super(Transaction, self).save(*args, **kwargs)

    def get_new_transaction_state(self):
        """
        Returns the next possible status and location of a transaction
        """
        status, location = self.status, self.location

        if status == self.PROCESSING and location == self.ORIGIN:
            return self.PROCESSING, self.ROUTABLE
        elif status == self.PROCESSING  and location == self.ROUTABLE:
            return self.COMPLETED, self.DESTINATION
        elif status == self.FIXING and location == self.ROUTABLE:
            return self.PROCESSING, self.ROUTABLE
        elif status == self.REFUNDING and location == self.ROUTABLE:
            return self.REFUNDED, self.ORIGIN

    def deactivate_transaction(self):
        self.is_active = False
        self.save()

    def error_transaction(self):
        self.status = Transaction.ERROR
        self.save()
    
    def move_transaction(self, new_status, new_location):
        self.status = new_status
        self.location = new_location
        self.save()

    class Meta:
        ordering = ('-created_at',)

from django.contrib import admin, messages

from django_object_actions import DjangoObjectActions

from api.models import Item, Transaction

class TransactionInline(admin.TabularInline):
    model = Transaction
    fields = ('id', 'status', 'location', 'is_active', 'created_at', 'updated_at')
    readonly_fields = ('id', 'created_at', 'updated_at')
    extra = 0


class ItemAdmin(DjangoObjectActions, admin.ModelAdmin):
    inlines = [
        TransactionInline,
    ]
    list_display = ('id', 'amount', 'created_at', 'updated_at', 'state')

    def refund(self, request, obj):
        trans = None
        try:
            trans = Transaction.objects.get(
                item__pk=obj.id, 
                is_active=True,
                status=Transaction.ERROR
            )
        except Transaction.DoesNotExist:
            self.message_user(
                request,
                "Action failed, Item has no transaction in error state", 
                level=messages.ERROR
            )
        
        if trans:
            # deactivate current active transaction in error state.
            trans.deactivate_transaction()

            # Create new item transaction 
            trans_obj = Transaction.objects.create(
                item_id=obj.id, 
                status="refunding",
                location="routable"
            )

            # update item state
            item_obj = Item.objects.get(pk=obj.id)
            item_obj.update_item_state(trans_obj.status)

            self.message_user(
                request,
                "Refunding Item transaction", 
                level=messages.SUCCESS
            )
        
    refund.label = "Refund" 
    change_actions = ('refund', )


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'status', 'location', 'created_at', 'updated_at', 'is_active')


admin.site.register(Item, ItemAdmin)
admin.site.register(Transaction, TransactionAdmin)

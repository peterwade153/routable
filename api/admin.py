from django.contrib import admin

from api.models import Item, Transaction

class TransactionInline(admin.TabularInline):
    model = Transaction
    fields = ('id', 'status', 'location', 'is_active', 'created_at', 'updated_at')
    readonly_fields = ('id', 'created_at', 'updated_at')
    extra = 0


class ItemAdmin(admin.ModelAdmin):
    inlines = [
        TransactionInline,
    ]
    list_display = ('id', 'amount', 'created_at', 'updated_at', 'state')


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'status', 'location', 'created_at', 'updated_at', 'is_active')


admin.site.register(Item, ItemAdmin)
admin.site.register(Transaction, TransactionAdmin)

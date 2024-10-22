from django.contrib import admin
from .models import Product, ProductTransaction

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price', 'unit_per_box', 'box_amount', 'box_remain')
    search_fields = ('name',)
    readonly_fields = ('box_amount', 'box_remain')

@admin.register(ProductTransaction)
class ProductTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'change', 'quantity_after_transaction', 'timestamp', 'description')
    search_fields = ('product__name', 'transaction_type', 'description')
    list_filter = ('transaction_type', 'timestamp')

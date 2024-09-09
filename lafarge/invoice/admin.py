from django.contrib import admin
from .models import Customer, Salesman, Deliveryman, Invoice, InvoiceItem, Product, ProductTransaction

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name', 'address')

@admin.register(Salesman)
class SalesmanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Deliveryman)
class DeliverymanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price', 'unit_per_box', 'box_amount', 'box_remain')
    search_fields = ('name',)
    readonly_fields = ('box_amount', 'box_remain')  # Make box_amount and box_remain read-only

@admin.register(ProductTransaction)
class ProductTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'change', 'quantity_after_transaction', 'timestamp', 'description')
    search_fields = ('product__name', 'transaction_type', 'description')
    list_filter = ('transaction_type', 'timestamp')

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ('sum_price', 'price')
    fields = ('product', 'quantity', 'net_price', 'price', 'sum_price')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'customer', 'delivery_date', 'payment_date', 'total_price')
    search_fields = ('number', 'customer__name')
    inlines = [InvoiceItemInline]
    readonly_fields = ('total_price',)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.save()

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'price', 'sum_price')
    search_fields = ('invoice__number', 'product__name')
    fields = ('invoice', 'product', 'quantity', 'net_price', 'sum_price')
    readonly_fields = ('invoice', 'product', 'quantity', 'net_price', 'sum_price')

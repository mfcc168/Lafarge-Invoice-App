from django.contrib import admin
from .models import Invoice, InvoiceItem

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ('sum_price', 'price')
    fields = ('product', 'quantity', 'net_price', 'price', 'sum_price', 'product_type')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    autocomplete_fields = ['customer']
    list_display = ('number', 'terms', 'customer', 'delivery_date', 'payment_date', 'total_price')
    search_fields = ('number', 'customer__name')
    inlines = [InvoiceItemInline]
    readonly_fields = ('total_price',)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.save()

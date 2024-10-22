from django.contrib import admin
from .models import Customer, Salesman, Deliveryman

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'care_of', 'address', 'telephone_number')
    search_fields = ('name', 'care_of', 'address', 'telephone_number')

@admin.register(Salesman)
class SalesmanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Deliveryman)
class DeliverymanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

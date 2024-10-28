import django_tables2 as tables
from django_filters import FilterSet, ModelChoiceFilter
from .models import Invoice, Customer
from django_tables2.utils import A

class CustomerTable(tables.Table):
    name = tables.LinkColumn('customer_detail', args=[A('name')], text=lambda record: record.name,
                               attrs={'a': {'class': 'text-decoration-none'}})
    class Meta:
        model = Customer
        attrs = {
            'class': 'table table-striped table-bordered',
            'th': {
                '_ordering': {
                    'orderable': 'sortable',  # Instead of `orderable`
                    'ascending': 'ascend',    # Instead of `asc`
                    'descending': 'descend'   # Instead of `desc`
                }
            }
        }
        fields = ("name", "care_of", "address", "office_hour", "telephone_number")

class CustomerFilter(FilterSet):

    class Meta:
        model = Customer
        fields = {
            "name": ["contains"],
            "care_of": ["contains"],
            "address": ["contains"],
            "telephone_number": ["contains"],
        }


class InvoiceTable(tables.Table):
    number = tables.LinkColumn('invoice_detail', args=[A('number')], text=lambda record: record.number,
                               attrs={'a': {'class': 'text-decoration-none'}})
    class Meta:
        model = Invoice
        attrs = {
            'class': 'table table-striped table-bordered',
            'th': {
                '_ordering': {
                    'orderable': 'sortable',  # Instead of `orderable`
                    'ascending': 'ascend',    # Instead of `asc`
                    'descending': 'descend'   # Instead of `desc`
                }
            }
        }
        order_by = '-id'
        fields = ("id", "number", "customer", "delivery_date", "payment_date", "salesman", "total_price")


class InvoiceFilter(FilterSet):
    customer = ModelChoiceFilter(queryset=Customer.objects.all(), label="Customer")

    class Meta:
        model = Invoice
        fields = {
            "number": ["contains"],
            "customer": ["exact"],  # Allow filtering by an exact customer match
            "delivery_date": ["gte", "lte"],
            "payment_date": ["gte", "lte"],
            "salesman": ["exact"],
        }
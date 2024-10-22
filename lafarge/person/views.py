from django.shortcuts import render, get_object_or_404
from .models import Customer

def customer_list(request):
    customers = Customer.objects.all().prefetch_related('invoice_set')
    context = {
        'customers': customers,
    }
    return render(request, 'customer/customer_list.html', context)

def customer_detail(request, customer_name):
    customer = get_object_or_404(Customer, name=customer_name)
    context = {
        'customer': customer,
    }
    return render(request, 'customer/customer_detail.html', context)

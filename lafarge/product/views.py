from django.shortcuts import render, get_object_or_404
from .models import Product, ProductTransaction

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product/product_list.html', {'products': products})

def product_transaction_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    transactions = ProductTransaction.objects.filter(product=product).order_by('-timestamp')
    return render(request, 'product/product_transaction_detail.html', {
        'product': product,
        'transactions': transactions
    })

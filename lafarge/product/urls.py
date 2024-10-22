from django.urls import path
from .views import product_list, product_transaction_detail

urlpatterns = [
    path('products/', product_list, name='product_list'),
    path('products/<int:product_id>/', product_transaction_detail, name='product_transaction_detail'),
]

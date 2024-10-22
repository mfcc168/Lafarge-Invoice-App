from django.urls import path
from .views import customer_list, customer_detail

urlpatterns = [
    path('customers/', customer_list, name='customer_list'),
    path('customer/<str:customer_name>/', customer_detail, name='customer_detail'),
]

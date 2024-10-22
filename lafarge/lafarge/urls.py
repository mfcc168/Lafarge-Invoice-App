from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('invoice.urls')),  # For home and invoice-related URLs
    path('', include('person.urls')),  # For person-related URLs
    path('', include('product.urls')),   # For product-related URLs
    path('', include('home.urls')),   # For home-related URLs
]

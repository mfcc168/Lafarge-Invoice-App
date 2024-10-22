from django.urls import path
from .views import invoice_list, invoice_detail, download_invoice_pdf

urlpatterns = [
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoice/<str:invoice_number>/', invoice_detail, name='invoice_detail'),
    path('invoice/<str:invoice_number>/download/', download_invoice_pdf, name='download_invoice_pdf'),
]

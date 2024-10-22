from django.shortcuts import render, get_object_or_404
from .models import Invoice
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
from .pdf_utils import draw_invoice_page

def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'invoice/invoice_list.html', {'invoices': invoices})

def invoice_detail(request, invoice_number):
    invoice = get_object_or_404(Invoice, number=invoice_number)
    context = {
        'invoice': invoice
    }
    return render(request, 'invoice/invoice_detail.html', context)

def download_invoice_pdf(request, invoice_number):
    invoice = get_object_or_404(Invoice, number=invoice_number)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    draw_invoice_page(pdf, invoice, "Original")
    pdf.showPage()
    draw_invoice_page(pdf, invoice, "Customer Copy")
    pdf.showPage()
    draw_invoice_page(pdf, invoice, "Company Copy")
    pdf.showPage()
    draw_invoice_page(pdf, invoice, "Poison Form")

    pdf.save()
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.number}.pdf"'

    return response

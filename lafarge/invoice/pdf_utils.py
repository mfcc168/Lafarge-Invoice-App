import os
from datetime import datetime

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A5
from reportlab.platypus import Table, TableStyle

from .check_utils import prefix_check


def draw_invoice_page(pdf, invoice, copy_type):
    """
    Draw the content of an invoice page in the PDF.

    Args:
        pdf: The ReportLab Canvas object.
        invoice: The Invoice object.
        copy_type: A string indicating the type of copy (e.g., "Original", "Customer Copy", "Company Copy", "Poison Form").
    """
    width, height = A4

    # Draw the background image
    if copy_type == "Poison Form":
        background_image_path = os.path.join(settings.STATIC_ROOT, 'PoisonForm.png')
    else:
        background_image_path = os.path.join(settings.STATIC_ROOT, 'Invoice.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    # Set title font and position based on the copy type
    if copy_type == "Customer Copy" or copy_type == "Company Copy":
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(385, height - 50, copy_type)

    elif copy_type == "Original":
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(460, height - 50, copy_type)

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.address.split("\n") if line.strip()]
    office_hour_lines = [line.strip() for line in invoice.customer.office_hour.split("\n") if line.strip()]
    pdf.setFont("Helvetica-Bold", 14)
    if prefix_check(invoice.customer.name.lower()):
        pdf.drawString(70, height - 215, f"SOLD TO: {invoice.customer.name}")
    else:
        pdf.drawString(70, height - 215, f"SOLD TO: Dr. {invoice.customer.name}")
    if invoice.customer.care_of:
        if prefix_check(invoice.customer.care_of.lower()):
            pdf.drawString(140, height - 235, f"C/O: {invoice.customer.care_of}")
        else:
            pdf.drawString(140, height - 235, f"C/O: Dr. {invoice.customer.care_of}")
    y_position = height - 255
    # Create a TextObject for multi-line address
    text_object = pdf.beginText(70, y_position)
    text_object.setFont("Helvetica", 10)
    for line in address_lines:
        text_object.textLine(line)

    text_object.textLine(
        f"Tel: {invoice.customer.telephone_number or ''}"
        f"{f' ({invoice.customer.contact_person})' if invoice.customer.contact_person else ''}"
    )

    text_object.textLine(f"Order No.: {invoice.order_number}" if invoice.order_number else '')
    text_object.textLine(f"Delivery To: {invoice.customer.delivery_to}" if invoice.customer.delivery_to else '')

    pdf.drawText(text_object)

    text_object = pdf.beginText(450, y_position)
    text_object.setFont("Helvetica", 10)
    for line in office_hour_lines:
        text_object.textLine(line)
    pdf.drawText(text_object)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(70, height - 70, f"Invoice No. : {invoice.number}")
    # Salesman and Date
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(70, height - 145 , f"Date : ")
    pdf.drawString(70, height - 165, f"Salesman : {invoice.salesman.name}")
    if copy_type != "Poison Form":
        pdf.drawString(70, height - 185, f"Terms : {invoice.terms}")

    # Table for Invoice Items
    if copy_type == "Poison Form":
        # Aggregate quantities for products with the same name
        product_quantities = {}
        for item in invoice.invoiceitem_set.all():
            product_name = item.product.name
            if product_name in product_quantities:
                product_quantities[product_name] += item.quantity
            else:
                product_quantities[product_name] = item.quantity

        # Prepare table data
        data = [["Quantity", "Product"]]
        for product_name, total_quantity in product_quantities.items():
            data.append([
                f"{total_quantity} {item.product.unit}",  # Use the unit from the last item processed
                product_name,
            ])

        # Configure table styles
        table = Table(data, colWidths=[50, 250])
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ]))

        # Position the table
        table.wrapOn(pdf, width, height)
        table.drawOn(pdf, 175, height - 450)

    else:
        # Define the data for the table
        data = [["Quantity", "Product", "Unit Price", "Amount"]]
        for item in invoice.invoiceitem_set.all():
            unit_price_display = (
                item.product_type if item.product_type in ["bonus", "sample"]
                else f"${item.net_price:,.2f} (Nett Price)" if item.net_price
                else f"${item.price:,.2f}"
            )
            unit_price_display += f"\n"

            product_name = item.product.name
            product_name += f"\n"
            if invoice.show_registration_code and item.product.registration_code:
                product_name += f"(Reg. No.: {item.product.registration_code})"
            if invoice.show_expiry_date and item.product.expiry_date:
                product_name += f" (Exp.: {item.product.expiry_date.strftime('%Y-%m-%d')})"

            data.append([
                f"{item.quantity} {item.product.unit}\n",
                product_name,
                unit_price_display,
                f"${item.sum_price:,.2f}\n" if item.sum_price != 0 else f"-\n"
            ])

        # Create the table
        table = Table(data, colWidths=[50, 250, 100, 100])
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ]))

        # Position the table
        table.wrapOn(pdf, width, height)
        table_width, table_height = table.wrap(0, 0)  # Get actual table height

        # Draw the table, positioning it to expand downward
        table.drawOn(pdf, 50, height - 350 - table_height)

        # Add total price at the bottom
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(400, height - 620, f"Total: ${invoice.total_price:,.2f}")


def draw_order_form_page(pdf, order):
    """
    Draw the content of an order form page in the PDF (A5 portrait).

    Args:
        pdf: The ReportLab Canvas object.
    """
    width, height = A5

    # Draw the background image
    background_image_path = os.path.join(settings.STATIC_ROOT, 'OrderForm.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    # Customer information
    pdf.setFont("Helvetica-Bold", 8)
    if prefix_check(order.customer.name.lower()):
        pdf.drawString(30, height - 100, f"From: {order.customer.name}")
    else:
        pdf.drawString(30, height - 100, f"From: Dr. {order.customer.name}")
    pdf.drawString(30, height - 120, f"To : LAFARGE CO., LTD.")
    pdf.drawString(30, height - 140, f"Date: {datetime.today().strftime('%Y-%m-%d')}")

    pdf.drawString(30, height - 180, "This is to place an order for the following medical product(s):")

    # Aggregate quantities for products with the same name
    product_quantities = {}
    for item in order.invoiceitem_set.all():
        product_name = item.product.name.split('(')[0].strip()  # strip lot no.
        if product_name in product_quantities:
            product_quantities[product_name] += item.quantity
        else:
            product_quantities[product_name] = item.quantity

    # Prepare table data
    data = [["Quantity", "Product"]]
    for product_name, total_quantity in product_quantities.items():
        data.append([
            f"{total_quantity} {item.product.unit}",  # Use the unit from the last item processed
            product_name,
        ])

    # Configure table styles
    table = Table(data, colWidths=[50, 250])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))

    # Position the table
    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 60, height - 300)
    if prefix_check(order.customer.name.lower()):
        pdf.drawString(30, height - 340, f"Please confirm by replying to {order.customer.name}")
    else:
        pdf.drawString(30, height - 340, f"Please confirm by replying to Dr. {order.customer.name}")
    pdf.drawString(30, height - 360, f"Tel:  {order.customer.telephone_number}")

import os
from datetime import datetime
from decimal import Decimal, ROUND_UP

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle

from .check_utils import prefix_check
from .encryption import encrypt_customer_id
from .qrcode import generate_whatsapp_qr_code


def draw_invoice_page_legacy(pdf, invoice):
    """
    Draw the content of an invoice page in the PDF.

    Args:
        pdf: The ReportLab Canvas object.
        invoice: The Invoice object.
    """
    width, height = A4

    # Draw the background image
    # background_image_path = os.path.join(settings.STATIC_ROOT, 'Invoice_Legacy.png')
    # pdf.drawImage(background_image_path, 0, 0, width, height)
    pdf.setFont("Times-Bold", 12)

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.address.split("\n") if line.strip()]
    delivery_address_lines = [line.strip() for line in invoice.customer.delivery_address.split("\n") if line.strip()]
    office_hour_lines = [line.strip() for line in invoice.customer.office_hour.split("\n") if line.strip()]

    y_position = height - 150 + 12
    text_object = pdf.beginText(100, y_position)
    text_object.setFont("Times-Roman", 12)
    if prefix_check(invoice.customer.name.lower()):
        text_object.textLine(f"{invoice.customer.name}")
    else:
        text_object.textLine(f"Dr. {invoice.customer.name}")
    if invoice.customer.care_of and not invoice.customer.hide_care_of:
        if prefix_check(invoice.customer.care_of.lower()):
            text_object.textLine(f"{invoice.customer.care_of}")
        else:
            text_object.textLine(f"C/O: Dr. {invoice.customer.care_of}")

    for line in address_lines:
        text_object.textLine(line)

    text_object.textLine(
        f"Tel: {invoice.customer.telephone_number or ''}"
        f"{f' ({invoice.customer.contact_person})' if invoice.customer.contact_person else ''}"
    )
    pdf.drawText(text_object)

    text_object = pdf.beginText(32, height - 440)
    text_object.setFont("Times-Roman", 10)
    if invoice.order_number:
        text_object.textLine(f"Order No.: {invoice.order_number}")
    if invoice.customer.delivery_to:
        text_object.textLine(f"Deliver To: {invoice.customer.delivery_to}")
    if invoice.customer.show_delivery_address:
        for line in delivery_address_lines:
            text_object.textLine(line)
    pdf.drawText(text_object)
    pdf.drawString(37, height - 510, f"** ALL GOODS ARE NON RETURNABLE **")

    if office_hour_lines:
        office_hour_height = 150
        if len(str(invoice.customer.name)) >= 40:
            office_hour_height = 165
        pdf.setFont("Times-Bold", 12)
        pdf.drawString(458, height - office_hour_height + 12, f"OFFICE HOURS:")
        text_object = pdf.beginText(458, height - office_hour_height - 15 + 12)
        text_object.setFont("Times-Roman", 10)
        for line in office_hour_lines:
            text_object.textLine(line)
        pdf.drawText(text_object)

    # Salesman and Date
    pdf.setFont("Times-Bold", 10)
    pdf.drawString(65, height - 100 + 5, f"{invoice.terms}")
    pdf.drawString(65, height - 120 + 5, f"{invoice.salesman.code}")

    # Table for Invoice Items
    # Define the data for the table
    data = [[" ", " ", " ", " "]]
    for item in invoice.invoiceitem_set.all():
        nett_display = ""
        if item.hide_nett == False:
            nett_display = " (Nett)"
        unit_price_display = (
            item.product_type if item.product_type in ["bonus", "sample"]
            else f"${(item.net_price / item.product.units_per_pack).quantize(Decimal('0.01'), rounding=ROUND_UP):,.2f} {nett_display}" if item.net_price
            else f"${(item.price / item.product.units_per_pack).quantize(Decimal('0.01'), rounding=ROUND_UP):,.2f}"
        )

        if invoice.customer.show_registration_code or invoice.customer.show_expiry_date:
            unit_price_display += f"\n"

            product_name = item.product.name
            product_name += f"\n"
            if invoice.customer.show_registration_code and item.product.registration_code:
                product_name += f"(Reg. No.: {item.product.registration_code})"
            if invoice.customer.show_expiry_date and item.product.expiry_date:
                product_name += f" (Exp.: {item.product.expiry_date.strftime('%Y-%b-%d')})"
            data.append([
                product_name,
                f"{float(item.quantity):g} {item.product.unit}\n",
                unit_price_display,
                f"${item.sum_price:,.2f}\n" if item.sum_price != 0 else f"-\n"
            ])
        else:
            data.append([
                item.product.name,
                f"{float(item.quantity):g} {item.product.unit}",
                unit_price_display,
                f"${item.sum_price:,.2f}" if item.sum_price != 0 else f"-"
            ])

    # Create the table
    table = Table(data, colWidths=[200, 122, 92, 100])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    # Position the table
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height

    # Draw the table, positioning it to expand downward
    table.drawOn(pdf, 37, height - 200 - table_height)

    # Add total price at the bottom
    pdf.setFont("Times-Bold", 14)
    pdf.drawString(460, height - 430, f"${invoice.total_price:,.2f}")


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
    elif copy_type == "Customer Copy":
        background_image_path = os.path.join(settings.STATIC_ROOT, 'CustomerCopy.png')
    elif copy_type == "Company Copy":
        background_image_path = os.path.join(settings.STATIC_ROOT, 'CompanyCopy.png')
    else:
        background_image_path = os.path.join(settings.STATIC_ROOT, 'Invoice.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)
    pdf.setFont("Helvetica-Bold", 12)

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.address.split("\n") if line.strip()]
    delivery_address_lines = [line.strip() for line in invoice.customer.delivery_address.split("\n") if line.strip()]
    office_hour_lines = [line.strip() for line in invoice.customer.office_hour.split("\n") if line.strip()]
    pdf.setFont("Helvetica-Bold", 10)
    if prefix_check(invoice.customer.name.lower()):
        pdf.drawString(50, height - 165, f"SOLD TO: {invoice.customer.name}")
    else:
        pdf.drawString(50, height - 165, f"SOLD TO: Dr. {invoice.customer.name}")
    if invoice.customer.care_of and not invoice.customer.hide_care_of:
        if prefix_check(invoice.customer.care_of.lower()):
            pdf.drawString(50, height - 185, f"{invoice.customer.care_of}")
        else:
            pdf.drawString(50, height - 185, f"C/O: Dr. {invoice.customer.care_of}")
    y_position = height - 205
    # Create a TextObject for multi-line address
    text_object = pdf.beginText(50, y_position)
    text_object.setFont("Helvetica", 10)
    for line in address_lines:
        text_object.textLine(line)

    text_object.textLine(
        f"Tel: {invoice.customer.telephone_number or ''}"
        f"{f' ({invoice.customer.contact_person})' if invoice.customer.contact_person else ''}"
    )
    if invoice.order_number:
        text_object.textLine(f"Order No.: {invoice.order_number}")
    if invoice.customer.delivery_to:
        text_object.textLine(f"Deliver To: {invoice.customer.delivery_to}")
    if invoice.customer.show_delivery_address:
        for line in delivery_address_lines:
            text_object.textLine(line)

    pdf.drawText(text_object)

    if office_hour_lines:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(450, height - 185, f"OFFICE HOURS:")
        text_object = pdf.beginText(450, y_position)
        text_object.setFont("Helvetica", 10)
        for line in office_hour_lines:
            text_object.textLine(line)
        pdf.drawText(text_object)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 53, f"Invoice No. : {invoice.number}")
    # Salesman and Date
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, height - 73, f"Date : ")
    pdf.drawString(50, height - 93, f"Salesman : {invoice.salesman.code}")
    if copy_type != "Poison Form":
        pdf.drawString(50, height - 113, f"Terms : {invoice.terms}")

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
        data = [["Product", "Quantity"]]
        for product_name, total_quantity in product_quantities.items():
            data.append([
                product_name,
                f"{float(total_quantity):g} {item.product.unit}",  # Use the unit from the last item processed
            ])

        # Configure table styles
        table = Table(data, colWidths=[250, 150])
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ]))

        # Position the table
        table.wrapOn(pdf, width, height)
        table_width, table_height = table.wrap(0, 0)  # Get actual table height

        # Draw the table, positioning it to expand downward
        table.drawOn(pdf, 50, height - 286 - table_height)

    else:
        # Define the data for the table
        data = [["Product", "Quantity", "Unit Price", "Amount"]]

        for item in invoice.invoiceitem_set.all():
            nett_display = ""
            if item.hide_nett == False:
                nett_display = " (Nett)"
            unit_price_display = (
                item.product_type if item.product_type in ["bonus", "sample"]
                else f"${(item.net_price / item.product.units_per_pack).quantize(Decimal('0.01'), rounding=ROUND_UP):,.2f} {nett_display}" if item.net_price
                else f"${(item.price / item.product.units_per_pack).quantize(Decimal('0.01'), rounding=ROUND_UP):,.2f}"
            )

            unit_price_display += f"\n"

            product_name = item.product.name
            product_name += f"\n"
            if invoice.customer.show_registration_code and item.product.registration_code:
                product_name += f"(Reg. No.: {item.product.registration_code})"
            if invoice.customer.show_expiry_date and item.product.expiry_date:
                product_name += f" (Exp.: {item.product.expiry_date.strftime('%Y-%b-%d')})"
            data.append([
                product_name,
                f"{float(item.quantity):g} {item.product.unit}\n",
                unit_price_display,
                f"${item.sum_price:,.2f}\n" if item.sum_price != 0 else f"-\n"
            ])

        # Create the table
        table = Table(data, colWidths=[200, 100, 100, 100])
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ]))

        # Position the table
        table.wrapOn(pdf, width, height)
        table_width, table_height = table.wrap(0, 0)  # Get actual table height

        # Draw the table, positioning it to expand downward
        table.drawOn(pdf, 60, height - 286 - table_height)

        # Add total price at the bottom
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawRightString(510, height - 600, f"Total: ${invoice.total_price:,.2f}")

        encrypted_customer_id = encrypt_customer_id(invoice.customer.id)
        qr_code_image = generate_whatsapp_qr_code("61028531", encrypted_customer_id)
        qr_code_reader = ImageReader(qr_code_image)
        pdf.drawImage(qr_code_reader, 50, height - 822, width=75, height=75)


def draw_order_form_page(pdf, order):
    """
    Draw the content of an order form page in the PDF (A5 portrait).

    Args:
        pdf: The ReportLab Canvas object.
        order: The Order object.
    """
    width, height = A5

    # Draw the background image
    background_image_path = os.path.join(settings.STATIC_ROOT, 'OrderForm.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    # Customer information
    pdf.setFont("Helvetica-Bold", 10)
    if order.customer.care_of:
        if prefix_check(order.customer.care_of.lower()):
            pdf.drawString(30, height - 100, f"From: {order.customer.care_of}")
        else:
            pdf.drawString(30, height - 100, f"From: Dr. {order.customer.care_of}")
    else:
        if prefix_check(order.customer.name.lower()):
            pdf.drawString(30, height - 100, f"From: {order.customer.name}")
        else:
            pdf.drawString(30, height - 100, f"From: Dr. {order.customer.name}")
    pdf.drawString(30, height - 120, f"To: LAFARGE CO., LTD.")
    pdf.drawString(30, height - 140, f"Date: {datetime.today().strftime('%Y-%b-%d')}")

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
    data = [["Product", "Quantity"]]
    for product_name, total_quantity in product_quantities.items():
        data.append([
            product_name,
            f"{float(total_quantity):g} {item.product.unit}",  # Use the unit from the last item processed
        ])

    # Configure table styles
    table = Table(data, colWidths=[150, 50])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))

    # Position the table to expand downward
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height
    table.drawOn(pdf, 110, height - 200 - table_height)  # Start lower for downward expansion

    # Footer
    if prefix_check(order.customer.name.lower()):
        pdf.drawString(30, height - 390, f"Please confirm by replying to {order.customer.name}")
    else:
        pdf.drawString(30, height - 390, f"Please confirm by replying to Dr. {order.customer.name}")
    pdf.drawString(30, height - 410, f"Tel:  {order.customer.telephone_number}")


def draw_sample_page(pdf, invoice):
    """
    Draw the content of an order form page in the PDF (A5 portrait).

    Args:
        pdf: The ReportLab Canvas object.
        order: The Order object.
    """
    width, height = A5

    # Draw the background image
    background_image_path = os.path.join(settings.STATIC_ROOT, 'Sample.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(30, height - 53, f"Invoice No. : {invoice.number}")
    pdf.drawString(250, height - 120, f"Date: ")

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.address.split("\n") if line.strip()]
    office_hour_lines = [line.strip() for line in invoice.customer.office_hour.split("\n") if line.strip()]
    pdf.setFont("Helvetica-Bold", 10)
    if invoice.customer.name != "Sample":
        if prefix_check(invoice.customer.name.lower()):
            pdf.drawString(30, height - 120, f"TO: {invoice.customer.name}")
        else:
            pdf.drawString(30, height - 120, f"TO: Dr. {invoice.customer.name}")
        if invoice.customer.care_of:
            if prefix_check(invoice.customer.care_of.lower()):
                pdf.drawString(30, height - 130, f"{invoice.customer.care_of}")
            else:
                pdf.drawString(30, height - 130, f"C/O: Dr. {invoice.customer.care_of}")
        y_position = height - 150
        # Create a TextObject for multi-line address
        text_object = pdf.beginText(30, y_position)
        text_object.setFont("Helvetica", 10)
        for line in address_lines:
            text_object.textLine(line)

        text_object.textLine(
            f"Tel: {invoice.customer.telephone_number or ''}"
            f"{f' ({invoice.customer.contact_person})' if invoice.customer.contact_person else ''}"
        )

        pdf.drawText(text_object)

        if office_hour_lines:
            pdf.setFont("Helvetica-Bold", 8)
            pdf.drawString(300, height - 140, f"OFFICE HOURS:")
            text_object = pdf.beginText(300, height - 150)
            text_object.setFont("Helvetica", 8)
            for line in office_hour_lines:
                text_object.textLine(line)
            pdf.drawText(text_object)

    # Aggregate quantities for products with the same name
    product_quantities = {}
    for item in invoice.invoiceitem_set.all():
        product_name = item.product.name
        if product_name in product_quantities:
            product_quantities[product_name] += item.quantity
        else:
            product_quantities[product_name] = item.quantity

    # Prepare table data
    data = [["Product", "Quantity"]]
    for product_name, total_quantity in product_quantities.items():
        data.append([
            product_name,
            f"{float(total_quantity):g} {item.product.unit}",  # Use the unit from the last item processed
        ])

    # Configure table styles
    table = Table(data, colWidths=[200, 50])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))

    # Position the table to expand downward
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height
    table.drawOn(pdf, 70, height - 200 - table_height)  # Start lower for downward expansion


def draw_statement_page(pdf, customer, unpaid_invoices):
    """
    Draw the content of an invoice page in the PDF.

    Args:
        pdf: The ReportLab Canvas object.
        invoice: The Invoice object.
    """
    width, height = A4

    # Draw the background image

    background_image_path = os.path.join(settings.STATIC_ROOT, 'Statement.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    # Customer information
    address_lines = [line.strip() for line in customer.address.split("\n") if line.strip()]
    statement_use_additonal_lines = ""
    if customer.statement_use_additonal_line:
        statement_use_additonal_lines = [line.strip() for line in customer.statement_use_additonal_line.split("\n") if
                                         line.strip()]
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, height - 105, f"Date: {datetime.today().strftime('%Y-%b-%d')}")
    if prefix_check(customer.name.lower()):
        pdf.drawString(60, height - 180, f"{customer.name}")
    else:
        pdf.drawString(60, height - 180, f"Dr. {customer.name}")
    if customer.care_of:
        if prefix_check(customer.care_of.lower()):
            pdf.drawString(60, height - 200, f"C/O: {customer.care_of}")
        else:
            pdf.drawString(60, height - 200, f"C/O: Dr. {customer.care_of}")
    y_position = height - 220
    # Create a TextObject for multi-line address
    text_object = pdf.beginText(60, y_position)
    text_object.setFont("Helvetica", 10)
    for line in address_lines:
        text_object.textLine(line)
    for line in statement_use_additonal_lines:
        text_object.textLine(line)
    pdf.drawText(text_object)

    # Table for Invoice Items
    # Define the data for the table
    data = [["Invoice Date", "Invoice No.", "Amount"]]
    total_unpaid = 0
    for invoice in unpaid_invoices:
        total_unpaid += invoice.total_price
        data.append([
            invoice.delivery_date,
            invoice.number,
            f"HK$ {invoice.total_price:,.2f}"
        ])
    data.append([
        "",
        "",
        f"Total: HK$ {total_unpaid:,.2f}"
    ])

    # Create the table
    table = Table(data, colWidths=[100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),  # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Body background color
        ('GRID', (0, 0), (-1, -2), 0.5, colors.black),  # Border around cells
    ]))

    # Position the table
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height

    # Draw the table, positioning it to expand downward
    table.drawOn(pdf, 60, height - 366 - table_height)


def draw_delivery_note(pdf, invoice):
    """
    Draw the content of an invoice page in the PDF.

    Args:
        pdf: The ReportLab Canvas object.
        invoice: The Invoice object.
    """
    width, height = A4

    background_image_path = os.path.join(settings.STATIC_ROOT, 'DeliveryNote.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.delivery_address.split("\n") if line.strip()]
    pdf.setFont("Helvetica-Bold", 10)
    if prefix_check(invoice.customer.delivery_to.lower()):
        pdf.drawString(50, height - 180, f"Deliver To: {invoice.customer.delivery_to}")
    else:
        pdf.drawString(50, height - 180, f"Deliver To: Dr. {invoice.customer.delivery_to}")
    if invoice.customer.care_of:
        if prefix_check(invoice.customer.care_of.lower()):
            pdf.drawString(50, height - 190, f"C/O: {invoice.customer.care_of}")
        else:
            pdf.drawString(50, height - 190, f"C/O: Dr. {invoice.customer.care_of}")
    y_position = height - 200
    # Create a TextObject for multi-line address
    text_object = pdf.beginText(50, y_position)
    text_object.setFont("Helvetica", 9)
    for line in address_lines:
        text_object.textLine(line)

    text_object.textLine(
        f"Tel: {invoice.customer.telephone_number or ''}"
        f"{f' ({invoice.customer.contact_person})' if invoice.customer.contact_person else ''}"
    )
    pdf.drawText(text_object)

    pdf.setFont("Helvetica-Bold", 10)
    text_object = pdf.beginText(450, y_position)
    text_object.setFont("Helvetica", 10)

    if invoice.order_number:
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, height - 53, f"Order No. : {invoice.order_number}")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 296, f"Invoice No. : {invoice.number}")
    # Salesman and Date
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, height - 105, f"Date: ")

    # Define the data for the table
    data = [["Product", "Quantity"]]
    for item in invoice.invoiceitem_set.all():

        product_name = item.product.name
        product_name += f"\n"
        if invoice.customer.show_registration_code and item.product.registration_code:
            product_name += f"(Reg. No.: {item.product.registration_code})"
        if invoice.customer.show_expiry_date and item.product.expiry_date:
            product_name += f" (Exp.: {item.product.expiry_date.strftime('%Y-%b-%d')})"

        data.append([
            product_name,
            f"{float(item.quantity):g} {item.product.unit}\n",
        ])

    # Create the table
    table = Table(data, colWidths=[250, 150])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))

    # Position the table
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height

    # Draw the table, positioning it to expand downward
    table.drawOn(pdf, 50, height - 306 - table_height)

    if prefix_check(invoice.customer.delivery_to.lower()):
        pdf.drawString(410, height - 670, f"{invoice.customer.delivery_to}")
    else:
        pdf.drawString(410, height - 670, f"{invoice.customer.delivery_to}")

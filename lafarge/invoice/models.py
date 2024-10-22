from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Update these imports to the new locations
from person.models import Customer, Salesman, Deliveryman
from product.models import Product, ProductTransaction

class Invoice(models.Model):
    number = models.CharField(max_length=50, unique=True)
    terms = models.CharField(max_length=50, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE)
    delivery_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    products = models.ManyToManyField(Product, through='InvoiceItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_total_price(self):
        total = sum(item.sum_price for item in self.invoiceitem_set.all())
        self.total_price = total

    def save(self, *args, **kwargs):
        self.calculate_total_price()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number

class InvoiceItem(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('sample', 'Sample'),
        ('bonus', 'Bonus'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sum_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default='normal')

    def save(self, *args, **kwargs):
        # Similar logic as before, with references to the new locations
        if self.pk:
            previous = InvoiceItem.objects.get(pk=self.pk)
            if previous.quantity != self.quantity:
                change = self.quantity - previous.quantity

                if previous.product_type:
                    self.product.quantity += previous.quantity
                if self.product_type:
                    self.product.quantity -= self.quantity

                ProductTransaction.objects.create(
                    product=self.product,
                    transaction_type='sale' if self.product_type == 'normal' else 'adjustment',
                    change=-change,
                    quantity_after_transaction=self.product.quantity,
                    description=f"{self.product_type.capitalize()} transaction in invoice #{self.invoice.number}"
                )
        else:
            if self.product_type:
                self.product.quantity -= self.quantity

            ProductTransaction.objects.create(
                product=self.product,
                transaction_type='sale',
                change=-self.quantity,
                quantity_after_transaction=self.product.quantity,
                description=f"{self.product_type.capitalize()} in invoice {self.invoice.number}"
            )

        self.product.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.product.quantity += self.quantity
        self.product.save()

        ProductTransaction.objects.create(
            product=self.product,
            transaction_type='restock',
            change=self.quantity,
            quantity_after_transaction=self.product.quantity,
            description=f"Restock due to deletion of {self.product_type} invoice item {self.invoice.number}"
        )

        super().delete(*args, **kwargs)

# Update signals
@receiver(post_save, sender=InvoiceItem)
def update_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()

@receiver(post_delete, sender=InvoiceItem)
def revert_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()

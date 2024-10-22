from django.db import models
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=0)
    unit_per_box = models.PositiveIntegerField(default=1)
    box_amount = models.PositiveIntegerField(default=0, editable=False)
    box_remain = models.PositiveIntegerField(default=0, editable=False)

    def save(self, *args, **kwargs):
        if self.unit_per_box > 0:
            self.box_amount, self.box_remain = divmod(self.quantity, self.unit_per_box)
        else:
            self.box_amount, self.box_remain = 0, self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductTransaction(models.Model):
    TRANSACTION_CHOICES = [
        ('sale', 'Sale'),
        ('restock', 'Restock'),
        ('adjustment', 'Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_CHOICES)
    change = models.IntegerField()
    quantity_after_transaction = models.PositiveIntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.transaction_type} ({self.change}) on {self.timestamp}"

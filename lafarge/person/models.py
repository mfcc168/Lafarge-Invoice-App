from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=255)
    care_of = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField()
    office_hour = models.TextField(blank=True, null=True)
    telephone_number = models.CharField(max_length=255, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Salesman(models.Model):
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code

class Deliveryman(models.Model):
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code

from django.db import models

from marketing.company.models import Company
from system.file_upload.models import FileUpload, ContentFile


# Create your models here.
class ProductType(models.Model):
    id = models.CharField(primary_key=True, max_length=10, unique=True)
    name = models.CharField(max_length=255)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products_type'


class RegistrationUnit(models.Model):
    unit = models.CharField(max_length=255)
    address = models.CharField(max_length=255)


class Producer(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)


class RegistrationCert(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    date_activated = models.DateField()
    date_expired = models.DateField()
    registered_unit = models.ForeignKey(RegistrationUnit, null=True, on_delete=models.SET_NULL)
    producer = models.ForeignKey(Producer, null=True, on_delete=models.SET_NULL)


class ProductCategory(models.Model):
    id = models.CharField(primary_key=True, max_length=12, unique=True)
    name = models.CharField(max_length=255)
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
    ingredient = models.CharField(max_length=255)
    amount = models.CharField(max_length=50)
    poison_group = models.CharField(max_length=50)
    registration = models.ForeignKey(RegistrationCert, null=True, on_delete=models.SET_NULL)
    company = models.ForeignKey(Company, null=True, on_delete=models.SET_NULL)
    amount_warning = models.IntegerField(default=0)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UseObject(models.Model):
    id = models.CharField(primary_key=True, max_length=64, unique=True)
    name = models.CharField(max_length=255)


class UseFor(models.Model):
    id = models.CharField(primary_key=True, max_length=64, unique=True)
    name = models.CharField(max_length=255)


class CategoryDetail(models.Model):
    cate_id = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    use_object = models.ForeignKey(UseObject, null=True, on_delete=models.SET_NULL)
    use_for = models.ForeignKey(UseFor, null=True, on_delete=models.SET_NULL)
    dosage = models.CharField(max_length=255)
    usage = models.CharField(max_length=255)


class Product(models.Model):
    id = models.CharField(primary_key=True, max_length=12, unique=True)
    name = models.CharField(max_length=255)
    price = models.BigIntegerField(default=0)
    quantity = models.IntegerField(default=1)
    category = models.CharField(max_length=24, null=True)
    main_id = models.CharField(max_length=24, null=True)
    created_by = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

from django.db import models

from marketing.product.models import Product


# Create your models here.
class PriceList(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    date_start = models.DateField(null=False, blank=False)
    date_end = models.DateField(null=False, blank=False)
    note = models.CharField(max_length=255, null=True, blank=True)
    products = models.ManyToManyField(Product, through='ProductPrice')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductPrice(models.Model):
    price_list = models.ForeignKey(PriceList, null=True, on_delete=models.SET_NULL)
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    point = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

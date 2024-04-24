from datetime import datetime

from django.db import models

from marketing.product.models import Product


# Create your models here.
class PriceList(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    date_start = models.DateField(null=False, blank=False)
    date_end = models.DateField(null=False, blank=False)
    note = models.CharField(max_length=255, null=True, blank=True)
    products = models.ManyToManyField(Product, through='ProductPrice')

    created_by = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        char_id = "PL"
        current_year = datetime.utcnow().year
        two_digit_year = str(current_year)[-2:]
        i = 1
        while PriceList.objects.filter(id=f"{char_id}{two_digit_year}{i:04d}").exists():
            i += 1
        if i > 9999:
            raise ValueError({'id': 'Out of index'})
        _id = f"{char_id}{two_digit_year}{i:04d}"
        self.id = _id
        return super().save(*args, **kwargs)


class ProductPrice(models.Model):
    price_list = models.ForeignKey(PriceList, null=True, on_delete=models.SET_NULL)
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    amount = models.IntegerField(null=False, default=0)
    point = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

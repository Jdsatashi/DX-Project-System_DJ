from datetime import datetime

from django.db import models

from account.models import User
from marketing.price_list.models import ProductPrice, PriceList
from marketing.product.models import Product


# Create your models here.
class Order(models.Model):
    id = models.CharField(max_length=24, primary_key=True)
    date_get = models.DateField()
    date_company_get = models.DateTimeField()
    client_id = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    date_delay = models.IntegerField(default=0)
    list_type = models.CharField(max_length=24, null=True)
    price_list_id = models.ForeignKey(PriceList, null=True, on_delete=models.CASCADE,
                                      related_name="order_price_list")

    # SO mean Special Offer
    is_so = models.BooleanField(null=True, default=False)
    id_so = models.CharField(null=True, max_length=255, default=None)
    id_offer_consider = models.CharField(null=True, max_length=255, default=None)

    created_by = models.CharField(max_length=64, null=True)
    note = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=24, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            start_char = 'MT'
            current_year = datetime.utcnow().year
            two_digit_year = str(current_year)[-2:]
            current_month = datetime.utcnow().month
            two_digit_month = str(current_month) if len(str(current_month)) >= 2 else f"{current_month:02d}"
            i = 1
            while Order.objects.filter(id=f"{start_char}{two_digit_year}{two_digit_month}{i:05d}").exists():
                i += 1
            if i > 99999:
                raise ValueError({'id': 'Out of index'})
            print(i)
            _id = f"{start_char}{two_digit_year}{two_digit_month}{i:05d}"
            print(_id)
            self.id = _id
            print(self.id)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.client_id}"


class OrderDetail(models.Model):
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_detail")
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_product")
    order_quantity = models.IntegerField(null=False, default=1)
    order_box = models.DecimalField(max_digits=8, decimal_places=2, null=False, default=0)
    point_per_box = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    price_list_so = models.DecimalField(max_digits=10, decimal_places=0, null=True)

import time
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models

from account.models import User
from marketing.price_list.models import ProductPrice, PriceList
from marketing.product.models import Product


# Create your models here.
class Order(models.Model):
    id = models.CharField(max_length=24, primary_key=True)
    date_get = models.DateField(null=True)
    date_company_get = models.DateTimeField(null=True)
    client_id = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    date_delay = models.IntegerField(default=0)
    list_type = models.CharField(max_length=24, null=True)
    price_list_id = models.ForeignKey(PriceList, null=True, on_delete=models.CASCADE,
                                      related_name="order_price_list")

    # SO mean Special Offer
    is_so = models.BooleanField(null=True, default=False)
    id_so = models.CharField(null=True, max_length=255, default=None)
    id_offer_consider = models.CharField(null=True, max_length=255, default=None)

    order_point = models.FloatField(null=True)
    order_price = models.FloatField(null=True)

    created_by = models.CharField(max_length=64, null=True)
    note = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=24, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.price_list_id:
            if self.created_at is None:
                self.created_at = datetime.utcnow()
            if not (self.price_list_id.date_start <= self.created_at.date() <= self.price_list_id.date_end):
                raise ValidationError(
                    f"Order date {self.created_at.date()} must be within the PriceList's date range from {self.price_list_id.date_start} to {self.price_list_id.date_end}.")

    def save(self, *args, **kwargs):
        start_time = time.time()
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
            _id = f"{start_char}{two_digit_year}{two_digit_month}{i:05d}"
            self.id = _id
            print(f"Complete create pk: {time.time() - start_time}")
        order_details = self.order_detail.all()
        for detail in order_details:
            if detail.point_get != 0 and detail.point_get is not None:
                self.order_point += detail.point_get
            if detail.product_price:
                self.order_price += detail.product_price
        if self.order_point:
            self.order_point = round(self.order_point, 5)
        if self.order_price:
            self.order_price = round(self.order_price, 5)
        self.clean()
        print(f"Complete save: {time.time() - start_time}")
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.client_id}"


class OrderDetail(models.Model):
    order_id = models.ForeignKey(Order, null=True, on_delete=models.CASCADE, related_name="order_detail")
    product_id = models.ForeignKey(Product, null=True, on_delete=models.CASCADE, related_name="order_product")
    order_quantity = models.IntegerField(null=False, default=1)
    order_box = models.FloatField(null=False, default=0)
    price_list_so = models.FloatField(null=True)
    note = models.CharField(max_length=255, null=True)
    product_price = models.BigIntegerField(null=True)
    point_get = models.FloatField(null=True)

    def save(self, *args, **kwargs):
        if self.order_box:
            self.order_box = round(self.order_box, 5)
        if self.point_get:
            self.point_get = round(self.point_get, 5)
        super().save(*args, **kwargs)

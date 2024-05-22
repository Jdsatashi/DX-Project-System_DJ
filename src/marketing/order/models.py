import time
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from account.models import User
from marketing.price_list.models import ProductPrice, PriceList, PointOfSeason, SpecialOffer, SpecialOfferProduct
from marketing.product.models import Product
from marketing.sale_statistic.models import SaleStatistic


# Create your models here.
class Order(models.Model):
    id = models.CharField(max_length=24, primary_key=True)
    date_get = models.DateField(null=True)
    date_company_get = models.DateTimeField(null=True)
    client_id = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    date_delay = models.IntegerField(default=0)
    list_type = models.CharField(max_length=24, null=True)
    price_list_id = models.ForeignKey(PriceList, null=True, on_delete=models.CASCADE, related_name="order_price_list")

    # SO mean Special Offer
    is_so = models.BooleanField(null=True, default=False)
    id_so = models.CharField(null=True, max_length=255, default=None)
    id_offer_consider = models.CharField(null=True, max_length=255, default=None)

    new_special_offer = models.ForeignKey(SpecialOffer, null=True, on_delete=models.CASCADE, related_name='orders')

    order_point = models.FloatField(null=True)
    order_price = models.FloatField(null=True, default=0)  # Default value to ensure it's not None

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
        if not self.pk:
            self.id = self.generate_pk()
        self.calculate_totals()
        super().save(*args, **kwargs)
        if kwargs.get('update_sale_statistic', True):
            SaleStatistic.objects.update_from_order(self)

    def calculate_totals(self):
        order_details = self.order_detail.aggregate(
            total_point=Sum('point_get'),
            total_price=Sum('product_price')
        )
        self.order_point = round(order_details['total_point'] or 0, 5)
        self.order_price = round(order_details['total_price'] or 0, 5)

    def generate_pk(self):
        start_char = 'MT'
        current_year = datetime.utcnow().year
        two_digit_year = str(current_year)[-2:]
        current_month = datetime.utcnow().month
        two_digit_month = str(current_month).zfill(2)
        prefix = f"{start_char}{two_digit_year}{two_digit_month}"
        latest_order = Order.objects.filter(id__startswith=prefix).order_by('-id').first()
        if latest_order:
            latest_id = int(latest_order.id[-5:]) + 1
        else:
            latest_id = 1
        if latest_id > 99999:
            raise ValueError({'id': 'Out of index'})
        return f"{prefix}{str(latest_id).zfill(5)}"


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
        # Validate if product order is in price list
        price_list = self.order_id.price_list_id
        product = self.product_id
        product_price = ProductPrice.objects.filter(product_id=product, price_list_id=price_list)
        if not product_price.exists():
            raise ValidationError(f"Product ({product.id}) - {product.name} not in PriceList {price_list.name}")
        so = self.order_id.new_special_offer
        if so is not None and not SpecialOfferProduct.objects.filter(special_offer=so, product=product).exists():
            raise ValidationError(f"Product ({product.id}) - {product.name} not in SpecialOffer {so.name}")
        # Rounded float number
        if self.order_box:
            self.order_box = round(self.order_box, 5)
        if self.point_get:
            self.point_get = round(self.point_get, 5)
        super().save(*args, **kwargs)

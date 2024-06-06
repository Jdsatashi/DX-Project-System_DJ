from datetime import datetime, date

from django.apps import apps
from django.db import models

from account.models import User
from marketing.livestream.models import LiveStream
from marketing.product.models import Product


# Create your models here.
class PriceList(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    date_start = models.DateField(null=False, blank=False)
    date_end = models.DateField(null=False, blank=False)
    note = models.CharField(max_length=255, null=True, blank=True)
    products = models.ManyToManyField(Product, through='ProductPrice')
    type = models.CharField(max_length=64, null=False, default='sub',
                            choices=(('main', 'main'), ('sub', 'sub')))

    status = models.CharField(null=True, max_length=24)

    created_by = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
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

    @staticmethod
    def get_main_pl():
        today = date.today()
        price_list = PriceList.objects.filter(
            date_start__lte=today,
            date_end__gte=today,
            type='main'
        ).first()
        return price_list

    def __str__(self):
        return f"{self.id} - {self.name}"


class ProductPrice(models.Model):
    price_list = models.ForeignKey(PriceList, null=True, on_delete=models.SET_NULL)
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    price = models.BigIntegerField(null=False, blank=False)
    quantity_in_box = models.IntegerField(null=False, default=0)
    point = models.FloatField(null=True, blank=True)


class PointOfSeason(models.Model):
    price_list = models.ForeignKey(PriceList, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    point = models.FloatField(null=True, blank=True, default=0)
    total_point = models.FloatField(null=True, blank=True, default=0)
    used_point = models.FloatField(null=True, blank=True, default=0)
    bonus_point = models.FloatField(null=True, blank=True, default=0)
    redundant = models.FloatField(null=True, blank=True, default=0)

    def auto_point(self, pl, user):
        if not PointOfSeason.objects.filter(price_list=pl, user=user).exists():
            Order = apps.get_model('order', 'Order')
            OrderDetail = apps.get_model('order', 'OrderDetail')
            user_orders = Order.objects.filter(client_id=user, price_list_id=pl)
            order_details = OrderDetail.objects.filter(order_id__in=user_orders)
            point, total_point = calculate_point(order_details, pl)

            self.point = point
            self.total_point = total_point


class SpecialOffer(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=255)
    time_start = models.DateTimeField(null=True)
    time_end = models.DateTimeField(null=True)

    price_list = models.ForeignKey(PriceList, null=True, on_delete=models.CASCADE, related_name='offers')
    product = models.ManyToManyField(Product, through='SpecialOfferProduct')

    type_list = models.CharField(max_length=24, null=False, default='manual')  # Chọn giữa ['manual',
    # 'consider_offer_user']
    live_stream = models.ForeignKey(LiveStream, null=True, on_delete=models.SET_NULL, related_name='offers')
    count_turnover = models.BooleanField(default=False)  # Khuyến mãi sẽ tính doanh số hay không

    target = models.BigIntegerField(null=False, default=0)
    quantity_can_use = models.FloatField(null=True)
    box_can_use = models.IntegerField(null=True)

    status = models.CharField(null=True, max_length=24)
    note = models.CharField(null=True, max_length=255)

    created_by = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            char_id = "SO"
            current_year = datetime.utcnow().year
            two_digit_year = str(current_year)[-2:]
            i = 1
            while SpecialOffer.objects.filter(id=f"{char_id}{two_digit_year}{i:04d}").exists():
                i += 1
            if i > 9999:
                raise ValueError({'id': 'Out of index'})
            _id = f"{char_id}{two_digit_year}{i:04d}"
            self.id = _id
        return super().save(*args, **kwargs)


class SpecialOfferProduct(models.Model):
    special_offer = models.ForeignKey(SpecialOffer, null=True, on_delete=models.CASCADE, related_name='special_offers')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='special_offers')
    price = models.BigIntegerField(null=True)
    point = models.FloatField(null=True)
    quantity_in_box = models.IntegerField(default=0)
    cashback = models.BigIntegerField(null=True)
    max_order_box = models.IntegerField(null=True)


def calculate_point(order_details, price_list):
    point = 0
    total_point = 0
    for order_detail in order_details:
        # if order_detail.point_get == 0:
        product = order_detail.product_id
        product_price = ProductPrice.objects.get(price_list=price_list, product=product)
        quantity = order_detail.order_quantity
        if product_price.point is not None or product_price.point != 0:
            order_point = product_price.point * (quantity / product_price.quantity_in_box)

            if order_detail.point_get == 0 or order_detail.point_get is None:
                order_detail.point_get = order_point
                order_detail.save()
            if order_detail.product_price == 0 or order_detail.product_price is None:
                order_detail.product_price = float(quantity) * float(product_price.price)
                order_detail.save()
            point += order_point
            total_point += order_point
    return point, total_point

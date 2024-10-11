from datetime import datetime, date, timedelta

from django.apps import apps
from django.db import models
from django.db.models import Q, Sum
from django.utils.timezone import make_aware

from account.models import User
from marketing.livestream.models import LiveStream
from marketing.product.models import Product
from system_func.models import PeriodSeason
from utils.helpers import self_id


# Create your models here.
class PriceList(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    date_start = models.DateField(null=False, blank=False)
    date_end = models.DateField(null=False, blank=False)
    note = models.CharField(max_length=255, null=True, blank=True)
    products = models.ManyToManyField(Product, through='ProductPrice')

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
        if not self.status:
            self.status = 'active'
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.name}"


class ProductPrice(models.Model):
    price_list = models.ForeignKey(PriceList, null=True, on_delete=models.SET_NULL)
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    price = models.BigIntegerField(null=False, blank=False)
    quantity_in_box = models.IntegerField(null=False, default=0)
    point = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if ProductPrice.objects.filter(price_list=self.price_list, product=self.product).exists():
            raise ValueError(f"Sản phẩm {self.product_id} đã có trong bảng giá {self.price_list_id}")
        return super().save(*args, **kwargs)


class SpecialOffer(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=255)
    time_start = models.DateTimeField(null=True)
    time_end = models.DateTimeField(null=True)

    product = models.ManyToManyField(Product, through='SpecialOfferProduct')

    type_list = models.CharField(max_length=24, null=False, default='manual')  # Chọn giữa ['manual',
    # 'consider_offer_user', 'template']
    live_stream = models.ForeignKey(LiveStream, null=True, on_delete=models.SET_NULL, related_name='offers')
    count_turnover = models.BooleanField(default=False)  # Khuyến mãi sẽ tính doanh số hay không

    target = models.BigIntegerField(null=False, default=0)
    quantity_can_use = models.IntegerField(null=True)
    box_can_use = models.FloatField(null=True)

    used = models.BooleanField(default=False)
    for_nvtt = models.BooleanField(default=False)

    priority = models.IntegerField(null=True)
    status = models.CharField(null=True, max_length=24)
    note = models.TextField(null=True)

    created_by = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.id = self_id('SO', SpecialOffer, 4, '%y%m')
        return super().save(*args, **kwargs)


class SpecialOfferProduct(models.Model):
    special_offer = models.ForeignKey(SpecialOffer, null=True, on_delete=models.CASCADE, related_name='special_offers')
    product = models.ForeignKey(Product, null=True, on_delete=models.CASCADE, related_name='special_offers')
    price = models.BigIntegerField(null=True)
    point = models.FloatField(null=True)
    quantity_in_box = models.IntegerField(default=0)
    cashback = models.BigIntegerField(null=True)
    max_order_box = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        if ProductPrice.objects.filter(price_list=self.special_offer, product=self.product).exists():
            raise ValueError(f"Sản phẩm {self.product_id} đã có trong ưu đãi {self.special_offer_id}")
        return super().save(*args, **kwargs)


def get_month_start_end(date):
    # Get the first day of the month
    month_start = date.replace(day=1)
    # Get the first day of the next month, then subtract one day to get the last day of the current month
    next_month = month_start.replace(month=date.month % 12 + 1, day=1)
    month_end = next_month - timedelta(days=1)
    return month_start, month_end


def calculate_turnover(user, date):
    Order = apps.get_model('order', 'Order')
    SaleStatistic = apps.get_model('sale_statistic', 'SaleStatistic')

    user_orders = Order.objects.filter(client_id=user.id)
    month_start, month_end = get_month_start_end(date)
    print(f"{month_start} | {month_end}")
    print(f"User orders: {user_orders.count()}")
    orders_in_month = user_orders.filter(
        Q(date_get__gte=month_start) & Q(date_get__lte=month_end)
        # & Q(Q(new_special_offer__isnull=True) & Q(new_special_offer__count_turnover=False))
    )

    turnover = sum(order.order_price for order in orders_in_month if order.status != 'deactivate')
    print(f"Test user: {user.id} | {orders_in_month.count()} - {turnover}")
    sale_stat, created = SaleStatistic.objects.get_or_create(
        user=user,
        month=month_start,
        defaults={
            'total_turnover': turnover,
            'used_turnover': 0,
            'available_turnover': turnover,
            'bonus_turnover': 0
        }
    )

    if not created:
        sale_stat.total_turnover = turnover + sale_stat.bonus_turnover
        sale_stat.available_turnover = turnover - sale_stat.used_turnover
        sale_stat.save()


def get_user_ordered(date):
    Order = apps.get_model('order', 'Order')
    User = apps.get_model('account', 'User')
    month_start, month_end = get_month_start_end(date)

    month_start = make_aware(month_start)
    month_end = make_aware(month_end)

    orders_in_month = Order.objects.filter(date_get__gte=month_start, date_get__lte=month_end)
    user_ids = orders_in_month.values_list('client_id', flat=True).distinct()

    users_ordered = User.objects.filter(id__in=user_ids)

    return users_ordered

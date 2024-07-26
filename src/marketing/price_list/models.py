from datetime import datetime, date, timedelta

from django.apps import apps
from django.db import models
from django.db.models import Q
from django.utils.timezone import make_aware

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
        if not self.status:
            self.status = 'active'
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

    def auto_point(self):
        Order = apps.get_model('order', 'Order')
        OrderDetail = apps.get_model('order', 'OrderDetail')
        user_orders = Order.objects.filter(client_id=self.user, price_list_id=self.price_list)
        order_details = OrderDetail.objects.filter(order_id__in=user_orders)
        point, total_point = calculate_point(order_details, self.price_list)
        print(f"Testing point: {point} - {total_point}")
        self.point = point
        self.total_point = total_point


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

    priority = models.IntegerField(null=True)
    status = models.CharField(null=True, max_length=24)
    note = models.TextField(null=True)

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
    product = models.ForeignKey(Product, null=True, on_delete=models.CASCADE, related_name='special_offers')
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


def test():
    date = datetime.today()

    users = get_user_ordered(date)
    for user in users:
        calculate_turnover(user, date)

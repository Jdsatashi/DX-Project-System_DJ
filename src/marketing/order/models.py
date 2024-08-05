import time
from datetime import datetime

from django.db import models
from django.db.models import Sum, Case, When, FloatField, F
from django.db.models.functions import Abs, Coalesce
from rest_framework.exceptions import ValidationError

from account.models import User
from marketing.price_list.models import ProductPrice, PriceList, PointOfSeason, SpecialOffer, SpecialOfferProduct
from marketing.product.models import Product
from marketing.sale_statistic.models import SaleStatistic
from utils.helpers import local_time


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
    nvtt_id = models.CharField(max_length=64, null=True)

    created_by = models.CharField(max_length=64, null=True)
    note = models.TextField(null=True)
    status = models.CharField(max_length=24, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.price_list_id:
            if self.date_get is None:
                self.date_get = local_time()
            if not (self.price_list_id.date_start <= self.date_get <= self.price_list_id.date_end):
                raise ValidationError(
                    f"Order date {self.date_get} must be between the PriceList's date range from {self.price_list_id.date_start} to {self.price_list_id.date_end}.")

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self._state.adding
        if not self.pk:
            self.id = self.generate_pk()
        if not self.nvtt_id and self.client_id:
            self.nvtt_id = self.client_id.clientprofile.nvtt_id
        if self.new_special_offer or self.id_so:
            self.is_so = True
        self.calculate_totals()
        super().save(*args, **kwargs)

        if is_new:
            update_sale_statistics_for_user(self.client_id)

    # def save(self, *args, **kwargs):
    #     is_new = self._state.adding
    #     if not self.pk:
    #         self.id = self.generate_pk()
    #     self.calculate_totals()
    #     super().save(*args, **kwargs)
    #
    #     if is_new:
    #         update_all_sale_statistics_for_user(self.client_id)
    # if kwargs.get('update_sale_statistic', True):
    #     SaleStatistic.objects.update_from_order(self)

    def calculate_totals(self):
        order_details = self.order_detail.aggregate(
            total_point=Sum('point_get'),
            total_price=Sum('product_price')
        )
        self.order_point = round(order_details['total_point'] or 0, 5)
        self.order_price = round(order_details['total_price'] or 0, 5)

    def generate_pk(self):
        start_char = 'MTN'
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
            raise ValidationError({'id': 'Out of index'})
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
        # price_list = self.order_id.price_list_id
        # product = self.product_id
        # product_price = ProductPrice.objects.filter(product_id=product, price_list_id=price_list)
        # if not product_price.exists():
        #     raise ValidationError(f"Product ({product.id}) - {product.name} not in PriceList {price_list.name}")
        # so = self.order_id.new_special_offer
        # if so is not None and not SpecialOfferProduct.objects.filter(special_offer=so, product=product).exists():
        #     raise ValidationError(f"Product ({product.id}) - {product.name} not in SpecialOffer {so.name}")
        # Rounded float number
        if self.order_box:
            self.order_box = round(self.order_box, 5)
        if self.point_get:
            self.point_get = round(self.point_get, 5)
        super().save(*args, **kwargs)


class OrderBackup(models.Model):
    order_id = models.CharField(max_length=255, null=True)
    date_get = models.CharField(max_length=255, null=True)
    date_company_get = models.CharField(max_length=255, null=True)
    client_id = models.CharField(max_length=255, null=True)
    date_delay = models.CharField(max_length=255, null=True)

    price_list_id = models.CharField(max_length=255, null=True)

    clientlv1_id = models.CharField(max_length=255, null=True)
    list_type = models.CharField(max_length=255, null=True)

    is_so = models.CharField(null=True, max_length=255, default=None)
    id_so = models.CharField(null=True, max_length=255, default=None)
    id_offer_consider = models.CharField(null=True, max_length=255, default=None)

    note = models.CharField(max_length=255, null=True)

    created_by = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(null=True)


class OrderBackupDetail(models.Model):
    order_id = models.CharField(max_length=255, null=True)
    product_id = models.CharField(max_length=255, null=True)
    order_quantity = models.IntegerField(null=False, default=1)
    order_box = models.FloatField(null=False, default=0)

    product_price = models.BigIntegerField(null=True)
    quantity_in_box = models.IntegerField(null=True)

    point_get = models.FloatField(null=True)
    price_list_so = models.FloatField(null=True)

    note = models.CharField(max_length=255, null=True)


def update_sale_statistics_for_user(user):
    # Lấy tất cả các Order của user
    orders = Order.objects.filter(client_id=user).order_by('created_at')

    # Tạo dictionary để lưu trữ doanh số cho mỗi tháng
    monthly_sales = {}
    bonus_turnover = 0

    for order in orders:
        # Lấy tháng từ ngày tạo Order
        order_month = order.created_at.date().replace(day=1)

        # Khởi tạo giá trị doanh số nếu chưa có trong dictionary
        if order_month not in monthly_sales:
            monthly_sales[order_month] = 0

        # Tính toán doanh số cho Order
        # if order.new_special_offer and order.new_special_offer.count_turnover is not False:
        #     monthly_sales[order_month] += order.order_price or 0
        if not order.new_special_offer:
            monthly_sales[order_month] += order.order_price or 0

    for month, total_turnover in monthly_sales.items():
        sale_statistic, created = SaleStatistic.objects.get_or_create(
            user=user,
            month=month,
            defaults={
                'total_turnover': total_turnover + bonus_turnover,
                'available_turnover': total_turnover + bonus_turnover,
            }
        )
        if not created:
            # Nếu SaleStatistic đã tồn tại, cập nhật giá trị
            SaleStatistic.objects.filter(pk=sale_statistic.pk).update(
                total_turnover=total_turnover + bonus_turnover,
                available_turnover=total_turnover + bonus_turnover - sale_statistic.used_turnover,
            )


def update_all_sale_statistics_for_user_2(user):
    # Lấy tất cả các Order của user
    orders = Order.objects.filter(client_id=user).order_by('created_at')

    # Tạo dictionary để lưu trữ doanh số cho mỗi tháng
    monthly_sales = {}

    for order in orders:
        # Lấy tháng từ ngày tạo Order
        order_month = order.created_at.date().replace(day=1)

        # Khởi tạo giá trị doanh số nếu chưa có trong dictionary
        if order_month not in monthly_sales:
            monthly_sales[order_month] = 0

        # Tính toán doanh số cho Order
        if order.new_special_offer and order.new_special_offer.count_turnover:
            monthly_sales[order_month] += order.order_price or 0
        elif not order.new_special_offer:
            monthly_sales[order_month] += order.order_price or 0

    # Cập nhật hoặc tạo mới SaleStatistic cho từng tháng
    for month, total_turnover in monthly_sales.items():
        sale_statistic, created = SaleStatistic.objects.get_or_create(
            user=user,
            month=month,
            defaults={
                'total_turnover': total_turnover,
                'available_turnover': total_turnover,
            }
        )
        if not created:
            # Nếu SaleStatistic đã tồn tại, cập nhật giá trị
            SaleStatistic.objects.filter(pk=sale_statistic.pk).update(
                total_turnover=total_turnover,
                available_turnover=total_turnover - sale_statistic.used_turnover,
            )


class SeasonalStatistic(models.Model):
    name = models.CharField(max_length=255, null=True)

    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)

    type = models.CharField(null=False, choices=(('point', 'điểm'), ('turnover', 'doanh số')))

    users = models.ManyToManyField(User, through='SeasonalStatisticUser', related_name='seasonal_statistics')

    note = models.TextField(null=True)

    created_by = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SeasonalStatisticUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='season_stats_user')
    season_stats = models.ForeignKey(SeasonalStatistic, on_delete=models.CASCADE, related_name='season_stats_user')

    turn_per_point = models.FloatField(null=True)
    turn_pick = models.IntegerField(null=True)
    redundant_point = models.FloatField(null=True)

    total_turnover = models.BigIntegerField(default=0)
    total_point = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        if self.pk is None:
            # It's a new record
            if SeasonalStatisticUser.objects.filter(user=self.user, season_stats=self.season_stats).exists():
                raise ValidationError({
                                          'message': f'SeasonalStatisticUser with user {self.user} and season stats {self.season_stats} already exists.'})
        else:
            # It's an update
            if SeasonalStatisticUser.objects.filter(user=self.user, season_stats=self.season_stats).exclude(
                    pk=self.pk).exists():
                raise ValidationError({
                                          'message': f'SeasonalStatisticUser with user {self.user} and season stats {self.season_stats} already exists in another record.'})
        super().save(*args, **kwargs)


def update_season_stats_users(season_stats_user: SeasonalStatisticUser):
    season_stats = season_stats_user.season_stats
    user = season_stats_user.user
    orders = Order.objects.filter(
        client_id=user, date_get__gte=season_stats.start_date, date_get__lte=season_stats.end_date)
    # Calculate total price and points from orders
    order_totals = orders.aggregate(
        total_price=Sum('order_price'),
        total_points=Sum('order_point')
    )
    # Calculate total quantity, boxes, and cashback from all order details related to the filtered orders
    # order_detail_totals = OrderDetail.objects.filter(
    #     order_id__in=orders
    # ).aggregate(
    #     total_quantity=Sum('order_quantity'),
    #     total_boxes=Sum('order_box'),
    #     total_cashback=Sum(F('order_quantity') * F('product_price'), output_field=models.FloatField())
    # )
    total_point = order_totals.get('total_points', 0) or 0
    turn_per_point = season_stats_user.turn_per_point or 0
    try:
        turn_pick = season_stats_user.turn_pick or total_point // turn_per_point
    except ZeroDivisionError:
        turn_pick = 0
    try:
        redundant_point = total_point % turn_per_point
    except ZeroDivisionError:
        redundant_point = 0

    season_stats_user.total_point = total_point
    season_stats_user.turn_pick = turn_pick
    season_stats_user.redundant_point = redundant_point
    return season_stats_user

import json
from datetime import datetime, timedelta, date

from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import Sum, FloatField, Q, QuerySet
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError

from account.models import User
from app import settings
from app.logs import app_log
from marketing.price_list.models import ProductPrice, PriceList, SpecialOffer, SpecialOfferProduct
from marketing.product.models import Product
from marketing.sale_statistic.models import SaleStatistic, SaleTarget
from system_func.models import PeriodSeason
from utils.constants import so_type
from utils.helpers import local_time


# Create your models here.
class Order(models.Model):
    id = models.CharField(max_length=24, primary_key=True)
    date_get = models.DateField(null=True)
    date_company_get = models.DateTimeField(null=True)
    client_id = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    date_delay = models.IntegerField(default=0)
    list_type = models.CharField(max_length=24, null=True)
    price_list_id = models.ForeignKey(PriceList, null=True, on_delete=models.SET_NULL, related_name="order_price_list")

    # SO mean Special Offer
    is_so = models.BooleanField(null=True, default=False)

    count_turnover = models.BooleanField(default=True)
    minus_so_box = models.BigIntegerField(null=True, default=None)

    new_special_offer = models.ForeignKey(SpecialOffer, null=True, on_delete=models.SET_NULL, related_name='orders')

    order_point = models.FloatField(null=True)
    order_price = models.FloatField(null=True, default=0)  # Default value to ensure it's not None
    nvtt_id = models.CharField(max_length=64, null=True)
    npp_id = models.CharField(max_length=64, null=True)

    created_by = models.CharField(max_length=64, null=True)
    note = models.TextField(null=True)
    status = models.CharField(max_length=24, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.price_list_id:
            if self.date_get is None:
                self.date_get = local_time()
            print(f"Type: {self.price_list_id.date_start} | {self.date_get} | {self.price_list_id.date_end}")
            if not (self.price_list_id.date_start <= self.date_get <= self.price_list_id.date_end):
                raise ValidationError(
                    f"Order date {self.date_get} must be between the PriceList's date range from {self.price_list_id.date_start} to {self.price_list_id.date_end}.")

    def save(self, *args, **kwargs):
        self.clean()
        if not self.pk:
            self.id = self.generate_pk()
        if not self.nvtt_id and self.client_id:
            try:
                self.nvtt_id = self.client_id.clientprofile.nvtt_id
            except AttributeError:
                pass
        if not self.npp_id and self.client_id:
            try:
                self.npp_id = self.client_id.clientprofile.client_lv1_id
            except AttributeError:
                pass
        if self.new_special_offer:
            self.is_so = True

        if self.note:
            try:
                # Ensure it's JSON-encoded string
                json_data = json.loads(self.note)
                note = json.dumps(json_data)
            except ValueError as e:
                note = {'notes': self.note}
                self.note = note
        if not self.order_point and not self.order_price:
            self.calculate_totals()
        super().save(*args, **kwargs)

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
    product_id = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL, related_name="order_product")
    order_quantity = models.IntegerField(null=False, default=1)
    order_box = models.FloatField(null=False, default=0)
    price_so = models.FloatField(null=True)
    note = models.TextField(null=True)
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


class OrderDelete(models.Model):
    order_id = models.CharField(max_length=255)
    date_get = models.DateField(null=True)
    date_company_get = models.DateTimeField(null=True)
    client_id = models.CharField(max_length=255, null=True)
    date_delay = models.IntegerField(default=0)
    list_type = models.CharField(max_length=24, null=True)
    price_list_id = models.CharField(max_length=255, null=True)

    # SO mean Special Offer
    is_so = models.BooleanField(null=True, default=False)

    count_turnover = models.BooleanField(default=True)
    minus_so_box = models.BigIntegerField(null=True, default=None)

    new_special_offer = models.CharField(max_length=255, null=True)

    order_point = models.FloatField(null=True)
    order_price = models.FloatField(null=True, default=0)  # Default value to ensure it's not None
    nvtt_id = models.CharField(max_length=64, null=True)
    npp_id = models.CharField(max_length=64, null=True)

    created_by = models.CharField(max_length=64, null=True)
    note = models.TextField(null=True)
    status = models.CharField(max_length=24, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderDetailDelete(models.Model):
    order_id = models.CharField(max_length=255, null=True)
    product_id = models.CharField(max_length=255, null=True)
    order_quantity = models.IntegerField(null=True, default=1)
    order_box = models.FloatField(null=True, default=0)
    price_so = models.FloatField(null=True)
    note = models.TextField(null=True)
    product_price = models.BigIntegerField(null=True)
    point_get = models.FloatField(null=True)


def create_or_get_sale_stats_user(user: User, month, breaking=False) -> SaleStatistic | None:
    try:
        old_month = None
        if breaking:
            return None
        if isinstance(month, str):
            month = parse_date(month)
        if not isinstance(month, date) or month.day != 1:
            # raise ValidationError("Month must be the first day of the month in 'YYYY-MM-DD' format.")
            old_month = month
        current_period = PeriodSeason.get_period_by_date('turnover')

        next_month = month + relativedelta(months=1)
        last_month = month - relativedelta(months=1)
        print(f"Test sale stats: {last_month} - {next_month}")
        if last_month < current_period.from_date:
            last_month = current_period.from_date
            breaking = True

        filter_month = month
        if old_month:
            filter_month = old_month
        query_filter = Q(client_id=user) & Q(date_get__range=(filter_month, next_month - timedelta(days=1)))
        filter_so_count = Q(Q(query_filter) & Q(
            Q(new_special_offer__count_turnover=True)
            # | Q(new_special_offer__type_list=so_type.consider_user)
            | Q(count_turnover=True)
        ))
        exclude_so = Q(status='deactivate')

        orders_count = Order.objects.filter(Q(filter_so_count) | Q(query_filter)).exclude(exclude_so)
        print(f"Order count: {orders_count.count()}")
        orders_so = (Order.objects.filter(query_filter & Q(Q(is_so=True))))

        total_used = 0
        sale_target, _ = SaleTarget.objects.get_or_create(month=month)
        for order in orders_so:
            result = OrderDetail.objects.filter(order_id=order).aggregate(total_order_box=Sum('order_box'))
            total_order_box = result.get('total_order_box', 0) or 0
            if order.new_special_offer:
                target = order.new_special_offer.target if order.new_special_offer.target > 0 else sale_target.month_target
            else:
                target = sale_target.month_target
            total_used += total_order_box * target
        sale_statistic: QuerySet = SaleStatistic.objects.filter(user=user, month=month)

        total_turnover = OrderDetail.objects.filter(order_id__in=orders_count).aggregate(total_price=Sum('product_price'))[
                             'total_price'] or 0

        if orders_count.exists() and sale_statistic.exists():
            print(f"Case 1")
            last_sale_stats = create_or_get_sale_stats_user(user, last_month, breaking)
            if last_sale_stats is not None:
                last_month_turnover = last_sale_stats.available_turnover
            else:
                last_month_turnover = 0

            sale_statistic: SaleStatistic = sale_statistic.first()
            if sale_statistic.last_month_turnover <= 0:
                sale_statistic.last_month_turnover = last_month_turnover
            sale_statistic.bonus_turnover = last_month_turnover % sale_target.month_target
            sale_statistic.total_turnover = total_turnover - sale_statistic.minus_turnover + sale_statistic.bonus_turnover
            sale_statistic.used_turnover = total_used
            sale_statistic.available_turnover = sale_statistic.total_turnover - sale_statistic.used_turnover
            sale_statistic.save()
            print(f"Check bonus: {sale_statistic.bonus_turnover}")
            return sale_statistic
        elif orders_count.exists() and not sale_statistic.exists():
            print(f"Case 2")
            last_sale_stats = create_or_get_sale_stats_user(user, last_month)
            if last_sale_stats is not None:
                last_month_turnover = last_sale_stats.available_turnover
            else:
                last_month_turnover = 0
            sale_statistic = SaleStatistic.objects.create(
                user=user, month=month, total_turnover=total_turnover,
                available_turnover=(total_turnover - total_used), last_month_turnover=last_month_turnover,
                used_turnover=total_used
            )
            return sale_statistic
        elif not orders_count.exists() and sale_statistic.exists():
            print(f"Case 3")
            sale_statistic = sale_statistic.first()
            sale_statistic.total_turnover = 0 - sale_statistic.minus_turnover + sale_statistic.bonus_turnover
            sale_statistic.used_turnover = 0
            sale_statistic.available_turnover = 0
            sale_statistic.save()
            return sale_statistic
        else:
            print(f"Case 4")
            return None
    except Exception as e:
        app_log.error(f"Get error create and return None")
        if settings.DEBUG:
            raise e
        else:
            return None


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
    orders = (Order.objects.filter(
        client_id=user, date_get__gte=season_stats.start_date, date_get__lte=season_stats.end_date)
              .exclude(status='deactivate'))
    # Calculate total price and points from orders
    order_details = OrderDetail.objects.filter(order_id__in=orders)

    # Tính tổng giá trị và điểm từ chi tiết đơn hàng
    totals = order_details.aggregate(
        total_price=Sum('product_price'),
        total_points=Sum('point_get')
    )

    total_price = totals.get('total_price', 0) or 0
    total_point = totals.get('total_points', 0) or 0
    # Calculate total quantity, boxes, and cashback from all order details related to the filtered orders
    # order_detail_totals = OrderDetail.objects.filter(
    #     order_id__in=orders
    # ).aggregate(
    #     total_quantity=Sum('order_quantity'),
    #     total_boxes=Sum('order_box'),
    #     total_cashback=Sum(F('order_quantity') * F('product_price'), output_field=models.FloatField())
    # )
    turn_per_point = season_stats_user.turn_per_point or 0

    try:
        turn_pick = season_stats_user.turn_pick or total_point // turn_per_point
    except ZeroDivisionError:
        turn_pick = None
    # if turn_pick:
    #     pickable = total_point // turn_per_point
    #     if not pickable + 1 > turn_pick > pickable - 1:
    #         turn_pick = pickable

    # turn_pick = season_stats_user.turn_pick or 0
    season_stats_user.turn_pick = turn_pick
    if season_stats_user.turn_pick:
        try:
            redundant_point = total_point % (turn_per_point * turn_pick) if total_point > (
                    turn_per_point * turn_pick) else 0
        except ZeroDivisionError:
            redundant_point = 0
    else:
        redundant_point = 0

    season_stats_user.total_point = round(total_point, 5)
    # season_stats_user.turn_pick = turn_pick
    season_stats_user.redundant_point = redundant_point
    return season_stats_user

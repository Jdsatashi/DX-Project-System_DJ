from django.db import models
from django.db.models import F
from django.utils import timezone

from account.models import User
from app.logs import app_log


# class SaleStatisticManager(models.Manager):
#     def update_from_order(self, order):
#         today = timezone.now().date()
#         first_day_of_month = today.replace(day=1)
#
#         sale_statistic, _ = self.get_or_create(
#             user=order.client_id,
#             month=first_day_of_month,
#         )
#
#         user_sale_statistic, _ = SaleStatistic.objects.get_or_create(user=order.client_id, month=first_day_of_month)
#         month_target = SaleTarget.objects.filter(month=first_day_of_month).first()
#
#         total_turnover_increase = order.order_price if not order.new_special_offer or (
#                 order.new_special_offer and order.new_special_offer.count_turnover) else 0
#         used_turnover = 0
#
#         if order.new_special_offer or order.is_so:
#             order_details = order.order_detail.all()
#             for order_detail in order_details:
#                 if order_detail.order_box:
#                     target = order.new_special_offer.target
#                     target = target if target > 0 else month_target.month_target
#                     app_log.info(f"Target: {target} | {order_detail.order_box}")
#                     used_turnover += target * order_detail.order_box
#
#         self.filter(pk=sale_statistic.pk).update(
#             total_turnover=F('total_turnover') + total_turnover_increase,
#             used_turnover=F('used_turnover') + used_turnover,
#             available_turnover=F('total_turnover') - F('used_turnover') + total_turnover_increase,
#         )
#
#     def update_from_order_2(self, order):
#         app_log.info("Looping")
#         today = timezone.now().date()
#         first_day_of_month = today.replace(day=1)
#
#         sale_statistic, _ = self.get_or_create(
#             user=order.client_id,
#             month=first_day_of_month,
#         )
#
#         if order.new_special_offer and order.new_special_offer.count_turnover:
#             total_turnover_increase = order.order_price
#         elif not order.new_special_offer:
#             total_turnover_increase = order.order_price
#         else:
#             total_turnover_increase = 0
#
#         self.filter(pk=sale_statistic.pk).update(
#             total_turnover=F('total_turnover') + total_turnover_increase,
#             available_turnover=F('total_turnover') - F('used_turnover') + total_turnover_increase,
#         )


class SaleTarget(models.Model):
    month = models.DateField()
    month_target = models.BigIntegerField(default=7000000)


# Create your models here.
class SaleStatistic(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    month = models.DateField()
    total_turnover = models.BigIntegerField(default=0)  # Tổng doanh số
    used_turnover = models.BigIntegerField(default=0)  # Doanh số đã sử dụng
    available_turnover = models.BigIntegerField(default=0)  # Doanh số còn lại

    last_month_turnover = models.BigIntegerField(default=0)  # Doanh số của tháng trước
    minus_turnover = models.BigIntegerField(default=0)  # Doanh số tuỳ chỉnh bị trừ
    bonus_turnover = models.BigIntegerField(default=0)  # Doanh số tuỳ chỉnh tăng hoặc dư

    # objects = SaleStatisticManager()

    class Meta:
        unique_together = ('user', 'month')

    def save(self, *args, **kwargs):
        # Get old instance if exists
        if self.pk:
            old_instance = SaleStatistic.objects.get(pk=self.pk)
            old_bonus_turnover = old_instance.bonus_turnover
            old_minus = old_instance.minus_turnover
        else:
            old_bonus_turnover = 0
            old_minus = 0

        # Calculate the difference in bonus_turnover
        bonus_turnover_diff = self.bonus_turnover - old_bonus_turnover
        old_minus_diff = self.minus_turnover - old_minus
        # Update total_turnover with the difference
        self.total_turnover += bonus_turnover_diff
        self.total_turnover -= old_minus_diff
        self.available_turnover = self.total_turnover - self.used_turnover

        sale_target, _ = SaleTarget.objects.get_or_create(month=self.month)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}: {self.user.username} - {self.month.strftime('%Y-%m')}"


class UserSaleStatistic(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.SET_NULL)
    turnover = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UsedTurnover(models.Model):
    user_sale_stats = models.ForeignKey(UserSaleStatistic, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=128, null=False, choices=(('special_offer', 'mua ưu đãi'), ('reset_month', 'đặt lại hàng tháng'), ('reset_season', 'đặt lại the vụ'), ('admin_fix', 'admin tuỳ chỉnh')))
    turnover = models.BigIntegerField(default=0)
    note = models.TextField(null=True)

    created_at = models.DateField(auto_now_add=True)

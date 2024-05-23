from django.db import models
from django.db.models import F
from django.utils import timezone

from account.models import User


class SaleStatisticManager(models.Manager):
    def update_from_order(self, order):
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)

        sale_statistic, _ = self.get_or_create(
            user=order.client_id,
            month=first_day_of_month,
        )

        total_turnover_increase = order.order_price if not order.new_special_offer or (
                    order.new_special_offer and order.new_special_offer.count_turnover) else 0

        self.filter(pk=sale_statistic.pk).update(
            total_turnover=F('total_turnover') + total_turnover_increase,
            available_turnover=F('total_turnover') - F('used_turnover') + total_turnover_increase,
        )

    def update_from_order_2(self, order):
        print("Looping")
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)

        sale_statistic, _ = self.get_or_create(
            user=order.client_id,
            month=first_day_of_month,
        )

        if order.new_special_offer and order.new_special_offer.count_turnover:
            total_turnover_increase = order.order_price
        elif not order.new_special_offer:
            total_turnover_increase = order.order_price
        else:
            total_turnover_increase = 0

        self.filter(pk=sale_statistic.pk).update(
            total_turnover=F('total_turnover') + total_turnover_increase,
            available_turnover=F('total_turnover') - F('used_turnover') + total_turnover_increase,
        )


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
    bonus_turnover = models.BigIntegerField(default=0)  # Doanh số được tăng hoặc dư

    objects = SaleStatisticManager()

    class Meta:
        unique_together = ('user', 'month')

    def save(self, *args, **kwargs):
        sale_target = SaleTarget.objects.get_or_create(month=self.month)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.month.strftime('%Y-%m')}"

# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from account.models import User
from .models import SaleStatistic, SaleTarget
from ..order.models import Order


@receiver(post_save, sender=User)
def create_monthly_turnover(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        SaleStatistic.objects.get_or_create(user=instance, month=first_day_of_month)


@receiver(post_save, sender=SaleStatistic)
def create_next_month_turnover(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        first_day_of_current_month = instance.month.replace(day=1)
        next_month = (first_day_of_current_month.replace(day=28) + timezone.timedelta(days=4)).replace(day=1)

        # Get the sale target for the current month
        current_month_target = SaleTarget.objects.filter(month=first_day_of_current_month).first()

        # If the sale target exists for the current month, calculate the bonus turnover
        if current_month_target:
            bonus_turnover = instance.available_turnover % current_month_target.month_target
        else:
            bonus_turnover = 0

        if not SaleStatistic.objects.filter(user=instance.user, month=next_month).exists():
            SaleStatistic.objects.create(user=instance.user, month=next_month, bonus_turnover=bonus_turnover)


@receiver(post_save, sender=Order)
def update_sale_statistic(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        sale_statistic, created = SaleStatistic.objects.get_or_create(user=instance.client_id, month=first_day_of_month)

        if instance.new_special_offer:
            if instance.new_special_offer.count_turnover:
                sale_statistic.total_turnover += instance.order_price
        else:
            sale_statistic.total_turnover += instance.order_price

        sale_statistic.available_turnover = sale_statistic.total_turnover - sale_statistic.used_turnover
        sale_statistic.save()

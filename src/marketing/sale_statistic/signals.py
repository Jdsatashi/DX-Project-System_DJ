from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from account.models import User
from marketing.order.models import Order
from marketing.sale_statistic.models import SaleStatistic

updating_statistic = False


@receiver(post_save, sender=User)
def create_monthly_turnover(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        SaleStatistic.objects.get_or_create(user=instance, month=first_day_of_month)


# @receiver(post_save, sender=SaleStatistic)
# def create_next_month_turnover(sender, instance, created, **kwargs):
#     if created:
#         today = timezone.now().date()
#         first_day_of_current_month = instance.month.replace(day=1)
#         next_month = (first_day_of_current_month.replace(day=28) + timezone.timedelta(days=4)).replace(day=1)
#
#         current_month_target = SaleTarget.objects.filter(month=first_day_of_current_month).first()
#         bonus_turnover = instance.available_turnover % current_month_target.month_target if current_month_target else 0
#
#         if not SaleStatistic.objects.filter(user=instance.user, month=next_month).exists():
#             SaleStatistic.objects.create(user=instance.user, month=next_month, bonus_turnover=bonus_turnover)

# @receiver(post_save, sender=Order)
# def update_sale_statistic(sender, instance, created, **kwargs):
#     global updating_statistic
#     if created and not updating_statistic:
#         print(f"Testing signals -----------")
#         updating_statistic = True
#         try:
#             print(f"HERE -----------")
#             SaleStatistic.objects.update_from_order(instance)
#         finally:
#             updating_statistic = False

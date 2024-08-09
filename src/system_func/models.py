from datetime import datetime, time

from django.apps import apps
from django.db import models
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from account.models import User


# Create your models here.
class PeriodSeason(models.Model):
    from_date = models.DateField(null=False)
    to_date = models.DateField(null=False)
    type = models.CharField(max_length=24, null=False)
    period = models.CharField(max_length=12, choices=(('current', 'hiện tại'), ('previous', 'mùa trước'), ('past', 'mùa cũ')), null=False)

    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_period_by_date(cls):
        today = datetime.now().date()
        current_period = cls.objects.filter(from_date__lte=today, to_date__gte=today).first()
        return current_period

    def save(self, *args, **kwargs):
        if self.period in ['current', 'previous']:
            existing = PeriodSeason.objects.filter(type=self.type, period=self.period).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(f"Đã tồn tại một bản ghi với type '{self.type}' và period '{self.period}'.")
        super().save(*args, **kwargs)


class PointOfSeason(models.Model):
    period = models.ForeignKey(PeriodSeason, on_delete=models.CASCADE, related_name='season_point')
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='season_point')
    point = models.FloatField(null=True, blank=True, default=0)
    total_point = models.FloatField(null=True, blank=True, default=0)
    used_point = models.FloatField(null=True, blank=True, default=0)
    bonus_point = models.FloatField(null=True, blank=True, default=0)
    redundant = models.FloatField(null=True, blank=True, default=0)

    def auto_point(self):
        Order = apps.get_model('order', 'Order')
        OrderDetail = apps.get_model('order', 'OrderDetail')
        current_period = PeriodSeason.objects.filter(type='point', period='current').first()
        start_date = current_period.from_date
        end_date = datetime.combine(current_period.to_date, time(23, 59, 59))

        user_orders = (Order.objects.filter(client_id=self.user, date_get__range=(start_date, end_date))
                       .exclude(status='deactivate'))

        order_details = OrderDetail.objects.filter(order_id__in=user_orders)

        total_points = order_details.aggregate(total_point=Sum('point_get'))['total_point'] or 0

        print(f"Total points: {total_points}")
        self.point = total_points
        self.total_point = total_points

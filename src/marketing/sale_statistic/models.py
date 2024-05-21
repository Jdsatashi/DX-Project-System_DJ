from django.db import models

from account.models import User


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

    class Meta:
        unique_together = ('user', 'month')

    def __str__(self):
        return f"{self.user.username} - {self.month.strftime('%Y-%m')}"

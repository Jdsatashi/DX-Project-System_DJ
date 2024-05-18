from datetime import datetime, timedelta

from django.db import models

from account.models import User, PhoneNumber
from marketing.product.models import Product


# Create your models here.
class LiveStream(models.Model):
    title = models.CharField(max_length=255)
    date_released = models.DateField()
    time_start = models.TimeField()
    live_url = models.CharField(max_length=255)

    status = models.CharField(null=True, max_length=24)
    note = models.CharField(null=True, max_length=255)

    created_by = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LiveStreamComment(models.Model):
    live_stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    phone = models.ForeignKey(PhoneNumber, null=True, on_delete=models.CASCADE)
    comment = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LiveStreamStatistic(models.Model):
    live_stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE)
    viewers = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    order_times = models.IntegerField(default=0)

    note = models.CharField(null=True, max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LiveStreamProductList(models.Model):
    live_stream = models.OneToOneField(LiveStream, on_delete=models.CASCADE)
    time_allow_order = models.FloatField(default=1)  # Thời gian được phép đặt hàng

    turn_order = models.IntegerField(default=1)     # Số lần đặt hàng của user

    note = models.CharField(null=True, max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LiveStreamProduct(models.Model):
    livestream_product_list = models.ForeignKey(LiveStreamProductList, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    price = models.BigIntegerField(default=0)
    point = models.FloatField(null=True, default=0)

    total_item = models.IntegerField(null=True)
    max_purchase = models.IntegerField(null=True)

    note = models.CharField(null=True, max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LiveStreamTracking(models.Model):
    live_stream = models.ForeignKey(LiveStream, null=True, on_delete=models.CASCADE)
    phone = models.ForeignKey(PhoneNumber, null=True, on_delete=models.CASCADE)
    time_join = models.TimeField(null=True)
    time_leave = models.TimeField(null=True)
    time_watch = models.TimeField(null=True)

    note = models.CharField(max_length=255, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.time_join and self.time_leave:
            # Convert time fields to datetime objects
            today = datetime.today()
            join_time = datetime.combine(today, self.time_join)
            leave_time = datetime.combine(today, self.time_leave)

            # Calculate the difference
            watch_duration = leave_time - join_time

            # Handle case where time_leave is past midnight
            if watch_duration < timedelta(0):
                watch_duration += timedelta(days=1)

            # Convert timedelta to time
            total_seconds = int(watch_duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.time_watch = datetime.strptime(f'{hours:02}:{minutes:02}:{seconds:02}', '%H:%M:%S').time()
        super().save(*args, **kwargs)

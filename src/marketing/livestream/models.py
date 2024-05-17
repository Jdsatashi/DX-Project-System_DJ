from django.db import models

from account.models import User


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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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

from django.db import models

from account.models import User
from system.file_upload.models import FileUpload


class Notification(models.Model):
    title = models.CharField(max_length=255, null=False)
    short_description = models.CharField(max_length=255, null=True)
    content = models.TextField(null=True)
    alert_date = models.DateField(null=True)
    alert_time = models.TimeField()
    type = models.CharField(max_length=64, null=True)
    note = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationUser(models.Model):
    notify = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='notification_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_users')
    status = models.CharField(max_length=64, default='unread')
    read_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationFile(models.Model):
    notify = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='notification_files')
    file = models.ForeignKey(FileUpload, null=True, on_delete=models.SET_NULL, related_name='notification_files')
    priority = models.IntegerField(null=True)
    note = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

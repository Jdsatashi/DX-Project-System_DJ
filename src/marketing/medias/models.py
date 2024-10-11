import traceback

from django.db import models
from django.db.models import UniqueConstraint, Max
from rest_framework.exceptions import ValidationError

from account.models import User
from app.logs import app_log
from system.file_upload.models import FileUpload
from utils.helpers import self_id


class Notification(models.Model):
    title = models.CharField(max_length=255, null=False)
    short_description = models.CharField(max_length=255, null=True)
    content = models.TextField(null=True)
    alert_date = models.DateField(null=True)
    alert_time = models.TimeField()
    type = models.CharField(max_length=64, null=True)   # [news, ]
    note = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=64, default='active')
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationUser(models.Model):
    notify = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='notification_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_users')
    status = models.CharField(max_length=64, default='unread')
    read_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if NotificationUser.objects.filter(notify=self.notify, user=self.user).exists():
            raise ValidationError({'error': f'notify {self.notify_id} and user {self.user_id} is existed'})


class NotificationFile(models.Model):
    notify = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='notification_files')
    file = models.ForeignKey(FileUpload, null=True, on_delete=models.SET_NULL, related_name='notification_files')
    priority = models.IntegerField(null=True)
    note = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        try:
            # Get all notify file
            notify_file = NotificationFile.objects.filter(notify=self.notify)
            # Validate id of notify
            if notify_file.exists() and self.id not in notify_file.exclude(id=self.id).values_list('id', flat=True):
                # Get all file priority
                prio_list = [p.priority for p in notify_file if p.priority is not None]
                # Check when self.priority in list
                if self.priority in prio_list:
                    # Get largest priority
                    max_num = max(prio_list)
                    max_num = max_num if max_num else 0
                    self.priority = max_num + 1
        except Exception as e:
            error_message = traceback.format_exc().splitlines()[-1]
            app_log.error(f"Error when save notification file: \n{e}")
            raise ValidationError({'error': 'cannot save notification file', 'error_message': error_message})
        super().save(*args, **kwargs)


class BannerDisplay(models.TextChoices):
    IMAGE = 'image', 'Image'
    VIDEO = 'video', 'Video'


class Banner(models.Model):
    id = models.CharField(max_length=32, primary_key=True, unique=True, null=False)
    name = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=255, null=True)

    type = models.CharField(max_length=64, null=True)

    display_type = models.CharField(max_length=24, choices=BannerDisplay.choices,
                                    default=BannerDisplay.IMAGE)

    note = models.TextField(null=True)

    created_by = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Create id for banner if not exist
        if not self.id:
            self.id = self_id('BANNER', self.__class__, 4)
        # Constraint Banner can be 1 type and display type for 1 object
        if Banner.objects.filter(type=self.type, display_type=self.display_type).exists():
            raise ValidationError({'error': 'banner with this ype and display type already existed'})
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'medias_banners'


class BannerItem(models.Model):
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE, related_name='banner_items')
    file = models.ForeignKey(FileUpload, null=True, on_delete=models.SET_NULL, related_name='banner_items')
    direct_url = models.CharField(max_length=255, null=True)

    video_url = models.CharField(max_length=255, null=True)

    title = models.CharField(max_length=255, null=True)
    priority = models.IntegerField(null=True)
    note = models.TextField(null=True)
    status = models.CharField(max_length=64, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['banner', 'priority'], name='unique_banner_priority')
        ]
        db_table = 'medias_banners_item'

    def save(self, *args, **kwargs):
        # Check priority
        if not self.priority:
            # Find self priority
            max_priority = BannerItem.objects.filter(banner=self.banner).aggregate(Max('priority'))['priority__max']
            if max_priority is not None:
                # If exist max priority, +1 current priority
                self.priority = max_priority + 1
            else:
                # When not have priority, default is 1
                self.priority = 1
        super().save(*args, **kwargs)

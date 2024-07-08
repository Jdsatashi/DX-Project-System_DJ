from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
from django.utils.timezone import make_aware

from marketing.medias.models import Notification
from marketing.medias.tasks import send_notification_task


@receiver(post_save, sender=Notification)
def schedule_notification_task(sender, instance, created, **kwargs):
    if created or instance.alert_date or instance.alert_time:
        # Tạo thời gian để lên lịch task
        alert_datetime = datetime.combine(instance.alert_date, instance.alert_time)
        aware_datetime = make_aware(alert_datetime)

        # Tính toán thời gian chờ trước khi chạy task
        time_until_alert = (aware_datetime - datetime.now()).total_seconds()
        if time_until_alert > 0:
            send_notification_task.apply_async((instance.id,), countdown=time_until_alert)

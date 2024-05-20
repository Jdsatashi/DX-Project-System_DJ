from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LiveStream, LiveStreamStatistic, LiveStreamPeekView


@receiver(post_save, sender=LiveStream)
def create_related_records(sender, instance, created, **kwargs):
    if created:
        LiveStreamStatistic.objects.create(live_stream=instance)
        LiveStreamPeekView.objects.create(live_stream=instance)

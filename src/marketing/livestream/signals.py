from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import LiveStream, LiveStreamStatistic, LiveStreamPeekView, LiveStreamTracking, LiveStreamOfferRegister, \
    LiveStreamComment


@receiver(post_save, sender=LiveStream)
def create_related_records(sender, instance, created, **kwargs):
    if created:
        LiveStreamStatistic.objects.create(live_stream=instance)
        LiveStreamPeekView.objects.create(live_stream=instance)


@receiver(post_save, sender=LiveStreamTracking)
@receiver(post_delete, sender=LiveStreamTracking)
def update_viewers(sender, instance, **kwargs):
    live_stream = instance.live_stream
    unique_viewers = LiveStreamTracking.objects.filter(live_stream=live_stream).values('phone').distinct().count()
    statistic, created = LiveStreamStatistic.objects.get_or_create(live_stream=live_stream)
    statistic.viewers = unique_viewers
    statistic.save()


@receiver(post_save, sender=LiveStreamOfferRegister)
@receiver(post_delete, sender=LiveStreamOfferRegister)
def update_order_times(sender, instance, **kwargs):
    live_stream = instance.live_stream
    unique_orders = LiveStreamOfferRegister.objects.filter(live_stream=live_stream, register=True).values('phone').distinct().count()
    statistic, created = LiveStreamStatistic.objects.get_or_create(live_stream=live_stream)
    statistic.order_times = unique_orders
    statistic.save()


@receiver(post_save, sender=LiveStreamComment)
@receiver(post_delete, sender=LiveStreamComment)
def update_comments(sender, instance, **kwargs):
    live_stream = instance.live_stream
    comment_count = LiveStreamComment.objects.filter(live_stream=live_stream).count()
    statistic, created = LiveStreamStatistic.objects.get_or_create(live_stream=live_stream)
    statistic.comments = comment_count
    statistic.save()

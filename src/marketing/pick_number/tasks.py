from celery import shared_task
from app.settings import pusher_client


@shared_task
def trigger_pusher(channel, event, data):
    pusher_client.trigger(channel, event, data)

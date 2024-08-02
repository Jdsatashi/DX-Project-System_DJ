import json
from datetime import datetime

from celery import shared_task
from django.utils.timezone import make_aware
from firebase_admin import messaging

from app.logs import app_log
from app.redis_db import redis_db


def send_firebase_notification3(title, body, registration_tokens, data):
    """
    Function to send a Firebase notification with custom data.

    :param title: Title of the notification
    :param body: Body of the notification
    :param registration_tokens: List of device registration tokens
    :param data: Additional custom data to send with the notification
    """
    app_log.info(f"Handling upload notify to FIREBASE")
    valid_tokens = [token for token in registration_tokens if isinstance(token, str) and token.strip()]

    if not valid_tokens:
        app_log.warning("No valid registration tokens provided. Exiting notification send.")
        return

    print(f"Handling upload notify to FIREBASE")
    msg_data = {
        'title': title,
        'body': body,
        'data': data,
        'registration_tokens': valid_tokens
    }
    app_log.info(f"Checking message data: f{msg_data}")
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        tokens=valid_tokens
    )
    try:
        # response = messaging.send_multicast(message)
        response = messaging.send_each_for_multicast(message)
        app_log.info(f"FIREBASE response: {response}")
        app_log.info('{0} messages were sent successfully'.format(response.success_count))
        print('{0} messages were sent successfully'.format(response.success_count))
        return response.success_count
    except Exception as e:
        app_log.error(f"Error sending notification to FIREBASE: {e}")
        raise None


@shared_task
def send_notification_task(notification_data):
    print("Task started")
    data = json.loads(notification_data)
    print(f"Loaded data for notification: {data}")
    response = send_firebase_notification3(data['title'], data['short_description'], data['registration_tokens'], data['my_data'])
    print(f"Notification sent with response: {response}")
    return response


def schedule_notification(notify_instance):
    now = make_aware(datetime.now())
    alert_datetime = make_aware(datetime.combine(notify_instance.alert_date, notify_instance.alert_time))
    app_log.info(f"Schedule function Notification")

    if alert_datetime <= now:
        # Send notification immediately
        send_notification_now(notify_instance)
    else:
        # Calculate delay for the notification
        delay = (alert_datetime - now).total_seconds()

        notification_data = {
            'title': notify_instance.title,
            'short_description': notify_instance.short_description,
            'registration_tokens': list(
                notify_instance.notification_users.values_list('user__device_token', flat=True)),
            'my_data': {
                "notification_id": str(notify_instance.id),
                "click_action": "click_action"
            }
        }

        # Serialize data and store in Redis or pass directly to Celery task
        notification_data_json = json.dumps(notification_data)
        redis_db.set(f"notification:{notify_instance.id}", notification_data_json)
        send_notification_task.apply_async((notification_data_json,), countdown=delay)


def send_notification_now(notify_instance):
    # Immediate notification logic
    registration_tokens = list(notify_instance.notification_users.values_list('user__device_token', flat=True))
    my_data = {
        "notification_id": str(notify_instance.id),
        "click_action": "click_action"
    }
    send_firebase_notification3(notify_instance.title, notify_instance.short_description, registration_tokens, my_data)

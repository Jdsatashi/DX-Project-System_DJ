from celery import shared_task
from firebase_admin import messaging

from app.logs import app_log
from marketing.medias.models import Notification


def send_firebase_notification(title, body, registration_tokens, data):
    """
    Function to send a Firebase notification with custom data.
    :param title: Title of the notification
    :param body: Body of the notification
    :param registration_tokens: List of device registration tokens
    :param data: Additional custom data to send with the notification
    """
    app_log.info(f"Handling upload notify to FIREBASE")

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        tokens=registration_tokens
    )
    app_log.info(f"Check data: {data}")
    try:
        # response = messaging.send_multicast(message)
        response = messaging.send_each_for_multicast(message)
        app_log.info(f"FIREBASE response: {response}")
        app_log.info('{0} messages were sent successfully'.format(response.success_count))
        return response
    except Exception as e:
        app_log.error(f"Error sending notification to FIREBASE: {e}")
        return None


@shared_task
def send_scheduled_notification(notify_id, notify, registration_tokens):
    # notification = Notification.objects.get(id=notify)

    my_data = {
        "notification_id": str(notify_id),
        "click_action": "click_action"
    }

    send_firebase_notification(notify['title'], notify['short_description'], registration_tokens, my_data)

from celery import shared_task

from app.logs import app_log
from marketing.medias.handles import send_firebase_notification
from marketing.medias.models import Notification, NotificationUser


@shared_task
def send_notification_task(notification_id):
    app_log.info(f'Starting task to send notification with ID: {notification_id}')
    try:
        notification = Notification.objects.get(id=notification_id)
        app_log.info(f'Notification found: {notification.title}')

        # Lấy danh sách người dùng và gửi thông báo
        users = NotificationUser.objects.filter(notify=notification)
        registration_tokens = list(users.values_list('user__device_token', flat=True))

        # Construct data
        my_data = {
            "notification_id": str(notification.id),
            "click_action": "click_action"
        }

        send_firebase_notification(notification.title, notification.short_description, registration_tokens, my_data)
        app_log.info(f'Notification sent successfully for ID: {notification_id}')
    except Notification.DoesNotExist:
        app_log.error(f'Notification with ID {notification_id} does not exist')
    except Exception as e:
        app_log.error(f'Error sending notification with ID {notification_id}: {str(e)}')

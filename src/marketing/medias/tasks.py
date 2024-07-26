from celery import shared_task
from django.db import transaction
from rest_framework.exceptions import ValidationError

from account.handlers.restrict_serializer import list_user_has_perm, list_group_has_perm, create_full_perm, add_perm
from account.models import User
from app.logs import app_log
from marketing.medias.handles import send_firebase_notification
from marketing.medias.models import Notification, NotificationUser, NotificationFile
from system.file_upload.models import FileUpload
from utils.constants import perm_actions


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

        test = send_firebase_notification(notification.title, notification.short_description, registration_tokens, my_data)
        print(f"Testing reponse send firebase: {test}")
        app_log.info(f'Notification sent successfully for ID: {notification_id}')
    except Notification.DoesNotExist:
        app_log.error(f'Notification with ID {notification_id} does not exist')
    except Exception as e:
        app_log.error(f'Error sending notification with ID {notification_id}: {str(e)}')


@shared_task
def send_notification_task2(notification_id, user_ids):
    app_log.info(f'Starting task to send notification with ID: {notification_id}')
    try:
        notification = Notification.objects.get(id=notification_id)
        app_log.info(f'Notification found: {notification.title}')

        # Lấy danh sách người dùng và gửi thông báo
        users = NotificationUser.objects.filter(notify=notification, user__id__in=user_ids)
        registration_tokens = list(users.values_list('user__device_token', flat=True))

        # Construct data
        my_data = {
            "notification_id": str(notification.id),
            "click_action": "click_action"
        }

        test = send_firebase_notification(notification.title, notification.short_description, registration_tokens, my_data)
        print(f"Testing reponse send firebase: {test}")
        app_log.info(f'Notification sent successfully for ID: {notification.id}')
    except Notification.DoesNotExist:
        app_log.error(f'Notification with ID {notification_id} does not exist')
    except Exception as e:
        app_log.error(f'Error sending notification with ID {notification_id}: {str(e)}')


@shared_task
def create_and_send_notification_task(validated_data, users, groups, files, notify_id=None):
    try:
        with transaction.atomic():
            if notify_id:
                notify = Notification.objects.get(id=notify_id)
                notify.alert_date = validated_data['alert_date']
                notify.alert_time = validated_data['alert_time']
                notify.title = validated_data['title']
                notify.content = validated_data['content']
                notify.save()
            else:
                notify = Notification.objects.create(**validated_data)

            list_perm = create_full_perm(Notification, notify.id, perm_actions['view'])

            existed_user_allow = list_user_has_perm(list_perm, True)
            existed_group_allow = list_group_has_perm(list_perm, True)

            add_perm({'type': 'users', 'data': users, 'existed': existed_user_allow}, list_perm, True)
            add_perm({'type': 'group', 'data': groups, 'existed': existed_group_allow}, list_perm, True)

            user_in_group = User.objects.filter(group_user__name__in=groups).exclude(is_superuser=True).distinct()
            users_from_ids = User.objects.filter(id__in=users).distinct()
            combined_users = user_in_group | users_from_ids
            distinct_users = combined_users.distinct()

            notify_users = [NotificationUser(notify=notify, user=user) for user in distinct_users]
            NotificationUser.objects.bulk_create(notify_users)

            for file in files:
                file_upload = FileUpload.objects.create(file=file)
                NotificationFile.objects.create(notify=notify, file=file_upload)

            send_notification_task.apply_async((notify.id,))
    except Exception as e:
        app_log.error(f"Error when handle notify and send FCM: \n{e}")
        raise ValidationError({'error': f'Error when handle notify {validated_data["title"]} and send FCM'})

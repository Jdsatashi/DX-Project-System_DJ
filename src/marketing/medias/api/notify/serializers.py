from datetime import datetime
from types import SimpleNamespace

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import make_aware, now
from rest_framework import serializers
from marketing.medias.tasks import send_scheduled_notification, send_firebase_notification
from account.handlers.restrict_serializer import create_full_perm, list_user_has_perm, \
    list_group_has_perm, add_perm
from account.models import Perm, User, GroupPerm, PhoneNumber
from app.logs import app_log
from marketing.medias.models import Notification, NotificationUser, NotificationFile
from system.file_upload.models import FileUpload
from utils.constants import perm_actions, admin_role
from utils.env import APP_SERVER
from firebase_admin import messaging

from utils.import_excel import get_user_list


def send_firebase_notification3(title, body, registration_tokens, data):
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


class NotificationSerializer(serializers.ModelSerializer):
    users = serializers.ListField(child=serializers.CharField(), write_only=True, allow_null=True, required=False)
    groups = serializers.ListField(child=serializers.CharField(), write_only=True, allow_null=True, required=False)
    files = serializers.ListField(child=serializers.FileField(), write_only=True, allow_null=True, required=False)
    import_users = serializers.FileField(required=False)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        users = NotificationUser.objects.filter(notify=instance).values_list('user__id', flat=True)

        # Get groups with specific permissions
        content_type = ContentType.objects.get_for_model(instance)
        perms = Perm.objects.filter(content_type=content_type, object_id=instance.id)
        groups = GroupPerm.objects.filter(perm__in=perms).exclude(name=admin_role).distinct().values_list('name',
                                                                                                          flat=True)

        # Get files from NotificationFile
        files = NotificationFile.objects.filter(notify=instance).values_list('file__file', flat=True)
        representation['users'] = list(users)
        representation['groups'] = list(groups)

        request = self.context.get('request')
        if request:
            representation['files'] = [request.build_absolute_uri(file.file.url) for file in
                                       FileUpload.objects.filter(file__in=files)]
        else:
            representation['files'] = [(APP_SERVER + file.file.url) if file.file.url else None for file in
                                       FileUpload.objects.filter(file__in=files)]

        return representation

    def create(self, validated_data):
        users = validated_data.pop('users', [])
        groups = validated_data.pop('groups', [])
        files = validated_data.pop('files', [])
        import_users = validated_data.pop('import_users', None)
        app_log.info(f"Number of files: {len(files)}")
        try:
            with transaction.atomic():
                notify = super().create(validated_data)
                # Create specific permission
                list_perm = create_full_perm(Notification, notify.id, perm_actions['view'])

                # Get user has perm
                existed_user_allow = list_user_has_perm(list_perm, True)
                existed_group_allow = list_group_has_perm(list_perm, True)
                # Processing add perm
                add_perm({'type': 'users', 'data': users, 'existed': existed_user_allow}, list_perm, True)
                add_perm({'type': 'group', 'data': groups, 'existed': existed_group_allow}, list_perm, True)

                # Get user from file except of choosing
                if import_users:
                    users = get_user_list(import_users)
                    distinct_users = User.objects.filter(id__in=users).distinct()
                else:
                    # Get all user from group
                    user_in_group = User.objects.filter(group_user__name__in=groups).exclude(is_superuser=True).distinct()

                    # Get user from list users id
                    users_from_ids = User.objects.filter(id__in=users).distinct()

                    # Merge 2 Queryset
                    combined_users = user_in_group | users_from_ids

                    # Get distinct user
                    distinct_users = combined_users.distinct()
                app_log.info(f"Count users: {distinct_users.count()}")
                # Add user to notification
                notify_users = [NotificationUser(notify=notify, user=user) for user in distinct_users]
                # Create notification of user
                NotificationUser.objects.bulk_create(notify_users)

                for file in files:
                    file_upload = FileUpload.objects.create(file=file)
                    NotificationFile.objects.create(notify=notify, file=file_upload)

                # Get registration tokens for FCM
                registration_tokens = list(PhoneNumber.objects.filter(user_id__in=distinct_users).values_list('device_code', flat=True))
                registration_tokens = [token for token in registration_tokens if token]

                # Send Firebase notification
                my_data = {
                    "notification_id": str(notify.id),
                    "click_action": "click_action"
                }

                time_now = timezone.now()
                alert_datetime = datetime.combine(notify.alert_date, notify.alert_time)
                # alert_datetime = timezone.make_aware(alert_datetime, timezone.get_current_timezone())

                delay = (alert_datetime - time_now).total_seconds()

                send_notify = {
                    'id': notify.id,
                    'title': notify.title,
                    'short_description': notify.short_description,
                }

                if delay < 10:
                    # Gửi thông báo ngay lập tức
                    send_scheduled_notification.apply_async((notify.id, send_notify, registration_tokens), countdown=10)
                else:
                    send_scheduled_notification.apply_async((notify.id, send_notify, registration_tokens), countdown=delay)

                # send_firebase_notification3(notify.title, notify.short_description, registration_tokens, my_data)
                # schedule_notification(notify)
                return notify
        except Exception as e:
            raise e

    def update(self, instance, validated_data):
        users = validated_data.pop('users', [])
        groups = validated_data.pop('groups', [])
        files = validated_data.pop('files', [])
        app_log.info(f"Number of files: {len(files)}")
        try:
            with transaction.atomic():
                notify = super().update(instance, validated_data)
                # Create specific permission
                list_perm = create_full_perm(Notification, instance.id, perm_actions['view'])

                # Get user has perm
                existed_user_allow = list_user_has_perm(list_perm, True)
                existed_group_allow = list_group_has_perm(list_perm, True)
                # Processing add perm
                add_perm({'type': 'users', 'data': users, 'existed': existed_user_allow}, list_perm, True)
                add_perm({'type': 'group', 'data': groups, 'existed': existed_group_allow}, list_perm, True)

                # Get all user from group
                user_in_group = User.objects.filter(group_user__name__in=groups).exclude(is_superuser=True).distinct()

                # Get user from list users id
                users_from_ids = User.objects.filter(id__in=users).distinct()

                # Merge 2 Queryset
                combined_users = user_in_group | users_from_ids

                # Get distinct user
                distinct_users = combined_users.distinct()

                # Remove users no longer associated with the notification
                current_notify_users = set(NotificationUser.objects.filter(notify=instance).values_list('user_id', flat=True))
                new_notify_users = set(distinct_users.values_list('id', flat=True))

                users_to_remove = current_notify_users - new_notify_users
                users_to_add = new_notify_users - current_notify_users

                # Remove users from notification
                if users_to_remove:
                    NotificationUser.objects.filter(notify=instance, user_id__in=users_to_remove).delete()

                # Add new users to notification
                if users_to_add:
                    new_notify_users_objs = [NotificationUser(notify=instance, user_id=user_id) for user_id in users_to_add]
                    NotificationUser.objects.bulk_create(new_notify_users_objs)

                # Handle files
                current_files = set(NotificationFile.objects.filter(notify=instance).values_list('file__file', flat=True))
                new_files = set(file.name for file in files)

                files_to_add = new_files - current_files
                files_to_keep = current_files & new_files

                # Delete files that are no longer associated with the notification
                NotificationFile.objects.filter(notify=instance).exclude(file__file__in=files_to_keep).delete()

                # Add new files
                for file in files:
                    if file.name in files_to_add:
                        file_upload = FileUpload.objects.create(file=file)
                        NotificationFile.objects.create(notify=instance, file=file_upload)

                # Get registration tokens for FCM
                registration_tokens = list(PhoneNumber.objects.filter(user_id__in=distinct_users).values_list('device_code', flat=True))
                registration_tokens = [token for token in registration_tokens if token]

                # Send Firebase notification
                my_data = {
                    "notification_id": str(notify.id),
                    "click_action": "click_action"
                }
                # send_firebase_notification3(notify.title, notify.short_description, registration_tokens, my_data)
                # schedule_notification(notify)
                return notify
        except Exception as e:
            raise e


class NotifyReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'short_description', 'alert_date', 'alert_time', 'content', 'type']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        # Get all file path
        files = NotificationFile.objects.filter(notify=instance).values_list('file__file', flat=True)
        # Create url path for file
        if request:
            file_list = [request.build_absolute_uri(file.file.url) for file in
                         FileUpload.objects.filter(file__in=files)]
        else:
            file_list = list()
            for file in FileUpload.objects.filter(file__in=files):
                file_url = APP_SERVER + file.file.url if file.file.url else None
                file_list.append(file_url)
        representation['files'] = file_list
        return representation


class NotificationUserSerializer(serializers.ModelSerializer):
    notify = NotifyReadSerializer()

    class Meta:
        model = NotificationUser
        exclude = ('id', 'updated_at')
        read_only_fields = ('id', 'updated_at', 'notify', 'user')


class NotificationFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationFile
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

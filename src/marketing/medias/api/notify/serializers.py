from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from firebase_admin import messaging
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from account.handlers.restrict_serializer import BaseRestrictSerializer, create_full_perm, list_user_has_perm, \
    list_group_has_perm, add_perm
from account.models import Perm, User, GroupPerm
from app.logs import app_log
from marketing.medias.models import Notification, NotificationUser, NotificationFile
from system.file_upload.models import FileUpload
from utils.constants import acquy, admin_role
from utils.env import APP_SERVER


def send_firebase_notification(title, body, registration_tokens):
    # Ensure registration_tokens is a list of strings
    registration_tokens = list(map(str, registration_tokens))

    if not registration_tokens:
        return None

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        tokens=registration_tokens,
    )
    response = messaging.send_each_for_multicast(message)
    return response


class NotificationSerializer(serializers.ModelSerializer):
    users = serializers.ListField(child=serializers.CharField(), write_only=True, allow_null=True, required=False)
    groups = serializers.ListField(child=serializers.CharField(), write_only=True, allow_null=True, required=False)
    files = serializers.ListField(child=serializers.FileField(), write_only=True, allow_null=True, required=False)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        users = NotificationUser.objects.filter(notify=instance).values_list('user__id', flat=True)
        content_type = ContentType.objects.get_for_model(instance)
        perms = Perm.objects.filter(content_type=content_type, object_id=instance.id)
        groups = GroupPerm.objects.filter(perm__in=perms).exclude(name=admin_role).distinct().values_list('name', flat=True)
        files = NotificationFile.objects.filter(notify=instance).values_list('file__file', flat=True)
        representation['users'] = list(users)
        representation['groups'] = list(groups)
        request = self.context.get('request')
        representation['files'] = [(APP_SERVER + file.file.url) if file.file.url else None for file in
                                   FileUpload.objects.filter(file__in=files)]
        return representation

    def create(self, validated_data):
        users = validated_data.pop('users', [])
        groups = validated_data.pop('groups', [])
        files = validated_data.pop('files', [])
        try:
            with transaction.atomic():
                notify = super().create(validated_data)
                list_perm = create_full_perm(Notification, notify.id, acquy['view'])
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

                # Send Firebase notification
                registration_tokens = distinct_users.values_list('device_token', flat=True)
                send_firebase_notification(notify.title, notify.short_description, registration_tokens)

                return notify
        except Exception as e:
            raise e

    def update(self, instance, validated_data):
        users = validated_data.pop('users', [])
        groups = validated_data.pop('groups', [])
        files = validated_data.pop('files', [])
        try:
            with transaction.atomic():
                first_notify_users = User.objects.filter(notification_users__notify=instance)
                existing_files = set(NotificationFile.objects.filter(notify=instance).values_list('file__file', flat=True))
                list_perm = create_full_perm(Notification, instance.id, acquy['view'])
                existed_user_allow = list_user_has_perm(list_perm, True)
                existed_group_allow = list_group_has_perm(list_perm, True)
                notify = super().update(instance, validated_data)
                add_perm({'type': 'users', 'data': users, 'existed': existed_user_allow}, list_perm, True)
                add_perm({'type': 'group', 'data': groups, 'existed': existed_group_allow}, list_perm, True)
                user_in_group = User.objects.filter(group_user__name__in=groups).exclude(is_superuser=True).distinct()
                users_from_ids = User.objects.filter(id__in=users).distinct()
                combined_users = user_in_group | users_from_ids
                distinct_users = combined_users.distinct()
                users_to_remove = first_notify_users.exclude(id__in=distinct_users)
                NotificationUser.objects.filter(notify=instance, user__in=users_to_remove).delete()
                notify_users = [NotificationUser(notify=notify, user=user) for user in distinct_users if not NotificationUser.objects.filter(notify=notify, user=user).exists()]
                NotificationUser.objects.bulk_create(notify_users)

                new_files = set(file.name for file in files)
                files_to_add = new_files - existing_files
                files_to_keep = existing_files & new_files
                NotificationFile.objects.filter(notify=notify).exclude(file__file__in=files_to_keep).delete()
                for file in files:
                    if file.name in files_to_add:
                        file_upload = FileUpload.objects.create(file=file)
                        NotificationFile.objects.create(notify=notify, file=file_upload)

                # Send Firebase notification
                registration_tokens = distinct_users.values_list('device_token', flat=True)
                send_firebase_notification(notify.title, notify.short_description, registration_tokens)

                return notify
        except Exception as e:
            raise e

    def send_firebase_notification(self, validated_data, users):
        title = validated_data.get('title')
        body = validated_data.get('short_description')
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            tokens=[user.device_token for user in users if user.device_token]
        )
        response = messaging.send_multicast(message)
        app_log.info(f'Successfully sent message: {response}')


class NotifyReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'short_description', 'alert_date', 'alert_time', 'content', 'type']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        app_log.info(f"In request")
        files = NotificationFile.objects.filter(notify=instance).values_list('file__file', flat=True)
        app_log.info(f"Test files: {files}")
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

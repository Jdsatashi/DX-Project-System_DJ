from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.timezone import make_aware, now
from rest_framework import serializers

from account.handlers.restrict_serializer import create_full_perm, list_user_has_perm, \
    list_group_has_perm, add_perm
from account.models import Perm, User, GroupPerm
from app.logs import app_log
from marketing.medias.models import Notification, NotificationUser, NotificationFile
from marketing.medias.tasks import send_notification_task
from system.file_upload.models import FileUpload
from utils.constants import perm_actions, admin_role
from utils.env import APP_SERVER


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

                # Get all user from group
                user_in_group = User.objects.filter(group_user__name__in=groups).exclude(is_superuser=True).distinct()

                # Get user from list users id
                users_from_ids = User.objects.filter(id__in=users).distinct()

                # Merge 2 Queryset
                combined_users = user_in_group | users_from_ids

                # Get distinct user
                distinct_users = combined_users.distinct()

                # Add user to notification
                notify_users = [NotificationUser(notify=notify, user=user) for user in distinct_users]
                # Create notification of user
                NotificationUser.objects.bulk_create(notify_users)

                for file in files:
                    file_upload = FileUpload.objects.create(file=file)
                    NotificationFile.objects.create(notify=notify, file=file_upload)

                # Setting time for alarm notification
                alert_datetime = datetime.combine(notify.alert_date, notify.alert_time)
                aware_datetime = make_aware(alert_datetime)
                time_until_alert = (aware_datetime - now()).total_seconds()
                # Timer count down when time > 0
                if time_until_alert > 0:
                    print(f"Time until alert: {time_until_alert}")
                    send_notification_task.apply_async((notify.id,), countdown=time_until_alert)
                # Send notification immediately
                else:
                    print(f"Else not time utils")
                    send_notification_task.apply_async((notify.id,))
                return notify
        except Exception as e:
            app_log.error(e)
            raise serializers.ValidationError({'error': 'gặp lỗi khi create notify'})

    def update(self, instance, validated_data):
        users = validated_data.pop('users', [])
        groups = validated_data.pop('groups', [])
        files = validated_data.pop('files', [])
        try:
            with transaction.atomic():
                first_notify_users = User.objects.filter(notification_users__notify=instance)
                existing_files = set(
                    NotificationFile.objects.filter(notify=instance).values_list('file__file', flat=True))
                # Create specific permission
                list_perm = create_full_perm(Notification, instance.id, perm_actions['view'])

                # Get user has perm
                existed_user_allow = list_user_has_perm(list_perm, True)
                existed_group_allow = list_group_has_perm(list_perm, True)
                app_log.info(f"User existing: {existed_user_allow} | Adding user: {users}")

                notify = super().update(instance, validated_data)

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

                # Find users to remove
                users_to_remove = first_notify_users.exclude(id__in=distinct_users)

                # Delete NotificationUser entries for users to remove
                NotificationUser.objects.filter(notify=instance, user__in=users_to_remove).delete()

                # Add user to notification
                notify_users = []
                for user in distinct_users:
                    if not NotificationUser.objects.filter(notify=notify, user=user).exists():
                        notify_users.append(NotificationUser(notify=notify, user=user))
                app_log.info(f"Test notify_user: {notify_users}")

                # Create notification of user
                NotificationUser.objects.bulk_create(notify_users)

                # Handle files, first clear old ones
                new_files = set(file.name for file in files)

                files_to_add = new_files - existing_files
                files_to_keep = existing_files & new_files

                # Delete files that are no longer associated with the notification
                NotificationFile.objects.filter(notify=notify).exclude(file__file__in=files_to_keep).delete()

                # Add new files
                for file in files:
                    if file.name in files_to_add:
                        file_upload = FileUpload.objects.create(file=file)
                        NotificationFile.objects.create(notify=notify, file=file_upload)

                # Setting time for alarm notification
                alert_datetime = datetime.combine(notify.alert_date, notify.alert_time)
                aware_datetime = make_aware(alert_datetime)
                time_until_alert = (aware_datetime - datetime.now()).total_seconds()
                # Timer count down when time > 0
                if time_until_alert > 0:
                    send_notification_task.apply_async((notify.id,), countdown=time_until_alert)
                # Send notification immediately
                else:
                    send_notification_task.apply_async((notify.id,))
                return notify
        except Exception as e:
            raise serializers.ValidationError({'error': 'gặp lỗi khi update notify'})


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

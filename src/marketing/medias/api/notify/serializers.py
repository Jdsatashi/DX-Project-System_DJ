from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from account.handlers.restrict_serializer import create_full_perm, list_user_has_perm, \
    list_group_has_perm, add_perm
from account.models import Perm, User, GroupPerm, PhoneNumber
from app.logs import app_log
from marketing.medias.models import Notification, NotificationUser, NotificationFile
from marketing.medias.tasks import send_scheduled_notification
from system.file_upload.models import FileUpload
from utils.constants import perm_actions, admin_role
from utils.env import APP_SERVER
from utils.import_excel import get_user_list

notifying_choices = (('all', 'all'), ('unread', 'unread'), ('only_new', 'only_new'),
                     ('new_and_unread', 'new_and_unread'), ('none', 'none'))


class NotificationSerializer(serializers.ModelSerializer):
    users = serializers.ListField(child=serializers.CharField(), write_only=True, allow_null=True, required=False)
    groups = serializers.ListField(child=serializers.CharField(), write_only=True, allow_null=True, required=False)
    files = serializers.ListField(child=serializers.FileField(), write_only=True, allow_null=True, required=False)
    import_users = serializers.FileField(required=False)
    notifying = serializers.ChoiceField(required=False, choices=notifying_choices)

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
        notifying = validated_data.pop('notifying', None)

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

                time_now = timezone.now()
                alert_datetime = datetime.combine(notify.alert_date, notify.alert_time)

                delay = (alert_datetime - time_now).total_seconds()

                send_notify = {
                    'id': notify.id,
                    'title': notify.title,
                    'short_description': notify.short_description,
                }

                if delay < 10:
                    send_scheduled_notification.apply_async((notify.id, send_notify, registration_tokens), countdown=10)
                else:
                    send_scheduled_notification.apply_async((notify.id, send_notify, registration_tokens), countdown=delay)

                return notify
        except Exception as e:
            if settings.DEBUG:
                raise e
            else:
                raise serializers.ValidationError({"message": f"got error when add notification: {e}"})

    def update(self, instance, validated_data):
        users = validated_data.pop('users', None)
        groups = validated_data.pop('groups', None)
        files = validated_data.pop('files', None)
        import_users = validated_data.pop('import_users', None)
        notifying = validated_data.pop('notifying', None)

        try:
            with transaction.atomic():
                # Cập nhật thông tin cơ bản của thông báo
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                instance.save()

                # Update permissions
                list_perm = create_full_perm(Notification, instance.id, perm_actions['view'])
                existed_user_allow = list_user_has_perm(list_perm, True)
                existed_group_allow = list_group_has_perm(list_perm, True)

                # Update permissions
                add_perm({'type': 'users', 'data': users, 'existed': existed_user_allow}, list_perm, True)
                add_perm({'type': 'group', 'data': groups, 'existed': existed_group_allow}, list_perm, True)

                # Xử lý người dùng từ tệp nếu có
                if import_users:
                    users = get_user_list(import_users)
                    combined_users = User.objects.filter(id__in=users)
                else:
                    user_in_group = User.objects.filter(group_user__name__in=groups).exclude(
                        is_superuser=True).distinct()
                    users_from_ids = User.objects.filter(id__in=users).distinct()
                    combined_users = user_in_group | users_from_ids
                distinct_users = combined_users.distinct()

                current_users = set(instance.notificationuser_set.all().values_list('user_id', flat=True))
                new_users = set(distinct_users.values_list('id', flat=True))
                to_add = new_users - current_users
                to_remove = current_users - new_users

                NotificationUser.objects.filter(notify=instance, user_id__in=to_remove).delete()
                NotificationUser.objects.bulk_create(
                    [NotificationUser(notify=instance, user_id=user_id) for user_id in to_add])

                # Handle files associated with the notification
                if files:
                    app_log.info(f"Number of files to update: {len(files)}")

                    NotificationFile.objects.filter(notify=instance).delete()
                    for file in files:
                        file_upload = FileUpload.objects.create(file=file)
                        NotificationFile.objects.create(notify=instance, file=file_upload)

                # Registration tokens for FCM might need updating too
                registration_tokens = list(
                    PhoneNumber.objects.filter(user_id__in=distinct_users).values_list('device_code', flat=True))
                registration_tokens = [token for token in registration_tokens if token]

                # Scheduling notifications similar to creation logic
                time_now = timezone.now()
                alert_datetime = datetime.combine(instance.alert_date, instance.alert_time)
                delay = (alert_datetime - time_now).total_seconds()

                send_notify = {'id': instance.id, 'title': instance.title,
                               'short_description': instance.short_description}

                if notifying:
                    if delay < 10:
                        send_scheduled_notification.apply_async((instance.id, send_notify, registration_tokens),
                                                                countdown=10)
                    else:
                        send_scheduled_notification.apply_async((instance.id, send_notify, registration_tokens),
                                                                countdown=delay)

                return instance
        except Exception as e:
            if settings.DEBUG:
                raise e
            else:
                raise serializers.ValidationError({"message": f"lỗi khi update thông báo {instance.pk}: {e}"})


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

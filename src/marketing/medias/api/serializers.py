from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from account.handlers.restrict_serializer import BaseRestrictSerializer, create_full_perm, list_user_has_perm, \
    list_group_has_perm, add_perm
from account.models import Perm, User, GroupPerm
from app.logs import app_log
from marketing.medias.models import Notification, NotificationUser, NotificationFile
from system.file_upload.models import FileUpload
from utils.constants import acquy, admin_role


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
        groups = GroupPerm.objects.filter(perm__in=perms).exclude(name=admin_role).distinct().values_list('name', flat=True)

        # Get files from NotificationFile
        files = NotificationFile.objects.filter(notify=instance).values_list('file__file', flat=True)
        representation['users'] = list(users)
        representation['groups'] = list(groups)
        representation['files'] = [file.url for file in FileUpload.objects.filter(file__in=files)]
        # request = self.context.get('request')
        # if (request and request.method == 'GET'
        #         and hasattr(request, 'resolver_match')
        #         and request.resolver_match.kwargs.get('pk')):
        #     representation['users'] = list(users)
        #     representation['groups'] = list(groups)
        #     representation['files'] = [file.url for file in FileUpload.objects.filter(file__in=files)]
        # else:
        #     user = list(users)[:5]
        #     representation['users'] = user + ['...'] if len(user) > 5 else user
        #     group = list(groups)[:5]
        #     representation['groups'] = group + ['...'] if len(group) > 5 else group
        #     file = [file.url for file in list(FileUpload.objects.filter(file__in=files))[:5]]
        #     representation['files'] = file + ['...'] if len(file) > 5 else file
        return representation

    def create(self, validated_data):
        users = validated_data.pop('users', [])
        groups = validated_data.pop('groups', [])
        files = validated_data.pop('files', [])
        try:
            with transaction.atomic():
                notify = super().create(validated_data)
                # Create specific permission
                list_perm = create_full_perm(Notification, notify.id, acquy['view'])

                # Get user has perm
                existed_user_allow = list_user_has_perm(list_perm, True)
                existed_group_allow = list_group_has_perm(list_perm, True)
                # Processing add perm
                add_perm({'type': 'users', 'data': users, 'existed': existed_user_allow}, list_perm,
                         True)
                add_perm({'type': 'group', 'data': groups, 'existed': existed_group_allow}, list_perm,
                         True)
                # Get all user from group
                user_in_group = User.objects.filter(group_user__name__in=groups
                                                    ).exclude(is_superuser=True).distinct()
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
                existing_files = set(
                    NotificationFile.objects.filter(notify=instance).values_list('file__file', flat=True))
                # Create specific permission
                list_perm = create_full_perm(Notification, instance.id, acquy['view'])

                # Get user has perm
                existed_user_allow = list_user_has_perm(list_perm, True)
                existed_group_allow = list_group_has_perm(list_perm, True)
                app_log.info(f"User existing: {existed_user_allow} | Adding user: {users}")

                notify = super().update(instance, validated_data)

                # Processing add perm
                add_perm({'type': 'users', 'data': users, 'existed': existed_user_allow}, list_perm,
                         True)
                add_perm({'type': 'group', 'data': groups, 'existed': existed_group_allow}, list_perm,
                         True)

                # Get all user from group
                user_in_group = User.objects.filter(group_user__name__in=groups
                                                    ).exclude(is_superuser=True).distinct()
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
                return notify
        except Exception as e:
            raise e


class NotifyReadSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'short_description', 'alert_date', 'alert_time', 'content', 'type', 'files']

    def get_files(self, obj):
        files = NotificationFile.objects.filter(notify=obj).values_list('file__file', flat=True)
        return [file.url for file in FileUpload.objects.filter(file__in=files)]


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

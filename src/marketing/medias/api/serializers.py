from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from account.handlers.restrict_serializer import BaseRestrictSerializer, create_full_perm, list_user_has_perm, \
    list_group_has_perm, add_perm
from account.models import Perm, User
from app.logs import app_log
from marketing.medias.models import Notification, NotificationUser, NotificationFile
from utils.constants import acquy


class NotificationSerializer(serializers.ModelSerializer):
    users = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)
    groups = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)
    files = serializers.ListField(child=serializers.FileField(), allow_null=True, required=False)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

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

                return notify
        except Exception as e:
            raise e


class NotificationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationUser
        fields = '__all__'
        read_only_fields = ('id', 'updated_at', 'notify', 'user')


class NotificationFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationFile
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

import asyncio

from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from account.models import Quyen, User
from draft.models import Draft, GroupDraft
from utils.constants import acquy


def handle_restrict(data, _id):
    if data.get('restrict', False):
        users = data.get('allow_users', [])
        print(users)
        actions = acquy.get('view')
        content = ContentType.objects.get_for_model(Draft)
        quyen_name = f'{content.app_label}_{content.model}_{_id}'
        list_quyen = list()
        for action in actions:
            _quyen_name = f"{action}_{quyen_name}"
            Quyen.objects.get_or_create(
                name=_quyen_name,
                mota=f"{action.capitalize()} {content.model} - {_id}",
                object_id=str(_id)
            )
            list_quyen.append(_quyen_name)
        for user_id in users:
            user = User.objects.get(id=user_id.upper())
            for quyen in list_quyen:
                user.quyenUser.add(quyen, through_defaults={'allow': True})


class DraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Draft
        fields = '__all__'

    restrict = serializers.BooleanField(required=False)
    allow_nhom = serializers.ListField(child=serializers.CharField(), required=False)
    restrict_nhom = serializers.ListField(child=serializers.CharField(), required=False)
    allow_users = serializers.ListField(child=serializers.CharField(), required=False)
    restrict_users = serializers.ListField(child=serializers.CharField(), required=False)

    def create(self, validated_data):
        print(validated_data)
        restrict = validated_data.pop('restrict', False)
        allow_nhom = validated_data.pop('allow_nhom', None)
        restrict_nhom = validated_data.pop('restrict_nhom', None)
        allow_users = validated_data.pop('allow_users', None)
        restrict_users = validated_data.pop('restrict_users', None)
        data = {
            "restrict": restrict,
            "allow_nhom": allow_nhom,
            "restrict_nhom": restrict_nhom,
            "allow_users": allow_users,
            "restrict_users": restrict_users,
        }
        print(data)
        if 'restrict' in validated_data:
            print("__________ TEST __________")
            print(restrict)
        instance = super().create(validated_data)
        if restrict:
            handle_restrict(data, instance.id)
        return instance


class GroupDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDraft
        fields = '__all__'

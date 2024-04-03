from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer, split_data
from account.models import Quyen, User, NhomQuyen
from draft.models import Draft, GroupDraft
from utils.constants import acquy


def handle_restrict(data, _id):
    if data.get('restrict', False):
        allow_users = data['allow_users'] if data['allow_users'] is not None else []
        allow_nhoms = data['allow_nhom'] if data['allow_nhom'] is not None else []
        restrict_users = data['restrict_users'] if data['restrict_users'] is not None else []
        restrict_nhoms = data['restrict_nhom'] if data['restrict_nhom'] is not None else []
        actions = acquy.get('full')
        user_actions = data.get('allow_actions', [])
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
            if action in acquy.get(user_actions[0]):
                list_quyen.append(_quyen_name)
        add_quyen_users(allow_users, list_quyen, True)
        add_quyen_nhoms(allow_nhoms, list_quyen, True)
        add_quyen_users(restrict_users, list_quyen, False)
        add_quyen_nhoms(restrict_nhoms, list_quyen, False)


def add_quyen_users(users: list, quyens: list, allow: bool):
    if len(users) > 0 and users[0] != '':
        for user_id in users:
            user = User.objects.get(id=user_id.upper())
            for quyen in quyens:
                user.quyenUser.add(quyen, through_defaults={'allow': allow})


def add_quyen_nhoms(nhoms: list, quyens: list, allow: bool):
    if len(nhoms) > 0 and nhoms[0] != '':
        for nhom_id in nhoms:
            nhom = NhomQuyen.objects.get(name=nhom_id)
            for quyen in quyens:
                nhom.quyen.add(quyen, through_defaults={'allow': allow})


class DraftSerializer(BaseRestrictSerializer):
    class Meta:
        model = Draft
        fields = '__all__'

    def create(self, validated_data):
        print(validated_data)
        data, quyen_data = split_data(validated_data)
        restrict = quyen_data.get('restrict')
        print(data)
        instance = super().create(data)
        if restrict:
            handle_restrict(quyen_data, instance.id)
        return instance


class GroupDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDraft
        fields = '__all__'

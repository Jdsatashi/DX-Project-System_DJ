from typing import Union, Type

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from rest_framework import serializers

from account.models import User, NhomQuyen, Quyen
from utils.constants import acquy


class BaseRestrictSerializer(serializers.ModelSerializer):
    # Get field for create quyen
    restrict = serializers.BooleanField(required=False)
    allow_actions = serializers.ListField(child=serializers.CharField(), required=False)
    allow_nhom = serializers.ListField(child=serializers.CharField(), required=False)
    restrict_nhom = serializers.ListField(child=serializers.CharField(), required=False)
    allow_users = serializers.ListField(child=serializers.CharField(), required=False)
    restrict_users = serializers.ListField(child=serializers.CharField(), required=False)

    @staticmethod
    def split_data(data):
        """ Remove unused fields for Model instances """
        restrict = data.pop('restrict', False)
        allow_actions = data.pop('allow_actions', [])
        allow_nhom = data.pop('allow_nhom', [])
        restrict_nhom = data.pop('restrict_nhom', [])
        allow_users = data.pop('allow_users', [])
        restrict_users = data.pop('restrict_users', [])
        # Add unuse fields for Model to Create quyen
        quyen_data = {
            "restrict": restrict,
            "allow_actions": allow_actions,
            "allow_nhom": allow_nhom,
            "restrict_nhom": restrict_nhom,
            "allow_users": allow_users,
            "restrict_users": restrict_users,
        }
        return data, quyen_data

    def handle_restrict(self, data: dict, _id: Union[str, int], model: Type[Model]) -> None:
        """ Handle adding rule Quyen for specific Object to created object """
        if data.get('restrict', False):
            # Get action for full CRUD quyen
            actions = acquy.get('full')
            user_actions = data.get('allow_actions', [])
            content = ContentType.objects.get_for_model(model)
            # Generate string quyen name
            quyen_name = f'{content.app_label}_{content.model}_{_id}'
            list_quyen = list()
            # Processing create quyen
            for action in actions:
                _quyen_name = f"{action}_{quyen_name}"
                Quyen.objects.get_or_create(
                    name=_quyen_name,
                    mota=f"{action.capitalize()} {content.model} - {_id}",
                    object_id=str(_id)
                )
                # Add quyen to list_quyen for register user/nhom
                if action in acquy.get(user_actions[0]):
                    list_quyen.append(_quyen_name)
            # Processing assign quyen to user/nhom
            self.add_quyen_users(data['allow_users'], list_quyen, True)
            self.add_quyen_nhoms(data['allow_nhom'], list_quyen, True)
            self.add_quyen_users(data['restrict_users'], list_quyen, False)
            self.add_quyen_nhoms(data['restrict_nhom'], list_quyen, False)

    @staticmethod
    def add_quyen_users(users: list, quyens: list, allow: bool):
        """ Add new quyens for user """
        if len(users) > 0 and users[0] != '':
            for user_id in users:
                user = User.objects.get(id=user_id.upper())
                for quyen in quyens:
                    user.quyenUser.add(quyen, through_defaults={'allow': allow})

    @staticmethod
    def add_quyen_nhoms(nhoms: list, quyens: list, allow: bool):
        """ Add new quyens for nhom_user """
        if len(nhoms) > 0 and nhoms[0] != '':
            for nhom_id in nhoms:
                nhom = NhomQuyen.objects.get(name=nhom_id)
                for quyen in quyens:
                    nhom.quyen.add(quyen, through_defaults={'allow': allow})

from typing import Union, Type

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from rest_framework import serializers

from account.models import User, GroupPerm, Perm
from utils.constants import acquy


class BaseRestrictSerializer(serializers.ModelSerializer):
    # Get field for create perm
    restrict = serializers.BooleanField(required=False, default=False, write_only=True)
    allow_actions = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    allow_nhom = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    restrict_nhom = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    allow_users = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    restrict_users = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)

    @staticmethod
    def split_data(data):
        """ Remove unused fields for Model instances """
        restrict = data.pop('restrict', False)
        allow_actions = data.pop('allow_actions', [])
        allow_nhom = data.pop('allow_nhom', [])
        restrict_nhom = data.pop('restrict_nhom', [])
        allow_users = data.pop('allow_users', [])
        restrict_users = data.pop('restrict_users', [])
        # Add unuse fields for Model to Create perm
        perm_data = {
            "restrict": restrict,
            "allow_actions": allow_actions,
            "allow_nhom": allow_nhom,
            "restrict_nhom": restrict_nhom,
            "allow_users": allow_users,
            "restrict_users": restrict_users,
        }
        return data, perm_data

    def handle_restrict(self, data: dict, _id: Union[str, int], model: Type[Model]) -> None:
        """ Handle adding rule Perm for specific Object to created object """
        if data.get('restrict', False):
            # Get action for full CRUD perm
            actions = acquy.get('full')
            user_actions = data.get('allow_actions', [])
            content = ContentType.objects.get_for_model(model)
            # Generate string perm name
            perm_name = f'{content.app_label}_{content.model}_{_id}'
            list_perm = list()
            # Processing create perm
            for action in actions:
                _perm_name = f"{action}_{perm_name}"
                Perm.objects.get_or_create(
                    name=_perm_name,
                    mota=f"{action.capitalize()} {content.model} - {_id}",
                    object_id=str(_id)
                )
                # Add perm to list_perm for register user/nhom
                if action in acquy.get(user_actions[0]):
                    list_perm.append(_perm_name)
            # Processing assign perm to user/nhom
            self.add_perm_users(data['allow_users'], list_perm, True)
            self.add_perm_nhoms(data['allow_nhom'], list_perm, True)
            self.add_perm_users(data['restrict_users'], list_perm, False)
            self.add_perm_nhoms(data['restrict_nhom'], list_perm, False)

    @staticmethod
    def add_perm_users(users: list, perms: list, allow: bool):
        """ Add new perms for user """
        if len(users) > 0 and users[0] != '':
            for user_id in users:
                user = User.objects.get(id=user_id.upper())
                for perm in perms:
                    user.permUser.add(perm, through_defaults={'allow': allow})

    @staticmethod
    def add_perm_nhoms(nhoms: list, perms: list, allow: bool):
        """ Add new perms for nhom_user """
        if len(nhoms) > 0 and nhoms[0] != '':
            for nhom_id in nhoms:
                nhom = GroupPerm.objects.get(name=nhom_id)
                for perm in perms:
                    nhom.perm.add(perm, through_defaults={'allow': allow})

from typing import Union, Type

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Model, Q
from rest_framework import serializers

from account.models import User, GroupPerm, Perm, UserPerm, UserGroupPerm
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
            perm_query = Q()
            # Processing create perm
            for action in actions:
                _perm_name = f"{action}_{perm_name}"
                Perm.objects.get_or_create(
                    name=_perm_name,
                    note=f"{action.capitalize()} {content.model} - {_id}",
                    object_id=str(_id)
                )
                # Add perm to list_perm for register user/nhom
                if action in acquy.get(user_actions[0]):
                    list_perm.append(_perm_name)
                    perm_query |= Q(name=perm_name)
            # Get users has perm
            user_perms = UserPerm.objects.filter(
                perm__name__in=list_perm,
                user__is_superuser=False
            ).distinct('user')
            # Create user_id list in which user has perm
            existed_user = []
            for user in user_perms:
                existed_user.append(user.user.id)

            # Get groups has perm
            group_perms = GroupPerm.objects.filter(Q(perm__name__in=list_perm)).distinct()
            # Create group name list in which group has perm
            existed_group = []
            for group in group_perms:
                existed_group.append(group.name)

            # Processing assign perm to user/nhom
            self.add_perm({'type': 'users', 'data': data['allow_users'], 'existed': existed_user}, list_perm, True)
            self.add_perm({'type': 'group', 'data': data['allow_nhom'], 'existed': existed_group}, list_perm, True)
            self.add_perm({'type': 'users', 'data': data['restrict_users'], 'existed': existed_user}, list_perm, False)
            self.add_perm({'type': 'group', 'data': data['restrict_nhom'], 'existed': existed_group}, list_perm, False)

    @staticmethod
    def add_perm(items: dict, perms: list, allow: bool):
        """ Add new perms for user """
        if len(items['data']) > 0 and items['data'][0] != '':
            # Get existed user/group permissions
            exited = items.get('existed', None)
            # Upper data id when type == 'users'
            items_data = [item.upper() for item in items['data']] if items['type'] == 'users' else items['data']
            # Remove Updating Restrict users/groups
            if exited:
                # Return users/groups that would be removed permissions
                items['existed'] = list(set(exited) - set(items_data))
            # Looping data update
            for item_data in items['data']:
                if items['type'] == 'users':
                    update_user_perm(item_data, perms, items, allow, exited)
                else:
                    update_group_perm(item_data, perms, items, allow, exited)
            if exited:
                # Looping no update data, remove its permissions
                for item_data in items['existed']:
                    if items['type'] == 'users':
                        update_user_perm(item_data, perms, items, allow, exited)
                    else:
                        update_group_perm(item_data, perms, items, allow, exited)


def update_user_perm(item_data, perms, items, allow, exited):
    # Try to get User
    try:
        user = User.objects.get(id=item_data.upper())
    # Return errors with fields error
    except models.ObjectDoesNotExist:
        field = 'allow' if allow else 'restrict'
        raise serializers.ValidationError({'error': f'Field error at "{field}_{items["type"]}"'})
    # Looping handle with permissions
    for perm in perms:
        is_perm = user.is_perm(perm)
        # Remove when permission is existed and User not in Updated list
        if exited is not None and is_perm and user.id in items['existed']:
            user.perm_user.remove(perm)
        elif is_perm:
            continue
        # Adding permissions to user
        else:
            user.perm_user.add(perm, through_defaults={'allow': allow})


def update_group_perm(item_data, perms, items, allow, exited):
    # Try to get Group
    try:
        group = GroupPerm.objects.get(name=item_data)
    # Return errors with fields error
    except models.ObjectDoesNotExist:
        field = 'allow' if allow else 'restrict'
        raise serializers.ValidationError({'error': f'Field error at "{field}_{items["type"]}"'})
    # Looping handle with permissions
    for perm in perms:
        is_perm = group.group_has_perm(perm)
        # Remove when permission is existed and Group not in Updated list
        if exited is not None and is_perm and group.name in items['existed']:
            group.perm.remove(perm)
        elif is_perm:
            continue
        # Adding permissions to group
        else:
            group.perm.add(perm, through_defaults={'allow': allow})

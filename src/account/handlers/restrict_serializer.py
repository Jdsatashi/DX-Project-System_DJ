import time
from typing import Union, Type

from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import Model, Q
from rest_framework import serializers

from account.models import User, GroupPerm, Perm, UserPerm, UserGroupPerm, PhoneNumber
from app.logs import app_log
from utils.constants import perm_actions, admin_role
from utils.helpers import phone_validate
from utils.import_excel import get_user_list


class BaseRestrictSerializer(serializers.ModelSerializer):
    # Get field for create perm
    restrict = serializers.BooleanField(required=False, default=False, write_only=True)
    allow_actions = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    allow_nhom = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    restrict_nhom = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    allow_users = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    restrict_users = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    hide_users = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    hide_groups = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    read_only_users = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    read_only_groups = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)

    def create(self, validated_data):
        try:
            with transaction.atomic():
                data, quyen_data = self.split_data(validated_data)
                instance = super().create(data)
                if quyen_data.get('restrict'):
                    self.handle_restrict(quyen_data, instance.id, self.Meta.model)
                return instance
        except Exception as e:
            raise e

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                data, quyen_data = self.split_data(validated_data)
                for attr, value in data.items():
                    setattr(instance, attr, value)
                instance.save()
                if quyen_data.get('restrict'):
                    self.handle_restrict(quyen_data, instance.id, self.Meta.model)
                return instance
        except Exception as e:
            raise e

    @staticmethod
    def split_data(data):
        """ Remove unused fields for Model instances """
        restrict = data.pop('restrict', False)
        allow_actions = data.pop('allow_actions', [])
        allow_nhom = data.pop('allow_nhom', [])
        restrict_nhom = data.pop('restrict_nhom', [])
        allow_users = data.pop('allow_users', [])
        restrict_users = data.pop('restrict_users', [])
        hide_users = data.pop('hide_users', [])
        hide_groups = data.pop('hide_groups', [])
        read_only_users = data.pop('read_only_users', [])
        read_only_groups = data.pop('read_only_groups', [])
        # Add un-use fields for Model to Create perm
        perm_data = {
            "restrict": restrict,
            "allow_actions": allow_actions,
            "allow_nhom": allow_nhom,
            "restrict_nhom": restrict_nhom,
            "allow_users": allow_users,
            "restrict_users": restrict_users,
            "hide_users": hide_users,
            "hide_groups": hide_groups,
            "read_only_users": read_only_users,
            "read_only_groups": read_only_groups,
        }
        return data, perm_data

    def handle_restrict_import_users_id(self, import_users, perm_data, user_actions):
        if import_users:
            users = perm_data.pop('allow_users', None)
            users_list = get_user_list(import_users)
            users_list = list(set(users_list))
            if users:
                for user in users:
                    if user.lower() not in users_list and user.upper() not in users_list:
                        users_list.append(user)
            perm_data['allow_users'] = users_list
            actions = perm_data.pop('allow_actions', None)
            # user_actions = [perm_actions['view'], perm_actions['create']]
            perm_data['allow_actions'] = user_actions
            perm_data['restrict'] = True

    def handle_restrict(self, data: dict, _id: Union[str, int], model: Type[Model]) -> None:
        """ Handle adding rule Perm for specific Object to created object """
        # Get action for full CRUD perm
        start_time = time.time()
        user_actions = data.get('allow_actions', [])
        list_perm = create_full_perm(model, _id, user_actions)
        # Get users has perm
        existed_user_allow = list_user_has_perm(list_perm, True)
        existed_user_restrict = list_user_has_perm(list_perm, False)
        existed_group_allow = list_group_has_perm(list_perm, True)
        existed_group_restrict = list_group_has_perm(list_perm, False)

        # Processing assign perm to user/nhom
        add_perm({'type': 'users', 'data': data['allow_users'], 'existed': existed_user_allow,
                  'hide': data['hide_users'], 'read_only': data['read_only_users']}, list_perm,
                 True)
        add_perm({'type': 'group', 'data': data['allow_nhom'], 'existed': existed_group_allow,
                  'hide': data['hide_groups'], 'read_only': data['read_only_groups']}, list_perm,
                 True)
        add_perm({'type': 'users', 'data': data['restrict_users'], 'existed': existed_user_restrict},
                 list_perm, False)
        add_perm({'type': 'group', 'data': data['restrict_nhom'], 'existed': existed_group_restrict},
                 list_perm, False)
        app_log.info(f"Complete add perm: {time.time() - start_time}")


def add_perm(items: dict, perms: [list, None], allow: bool):
    """ Add new perms for user """
    if items['data']:
        # Get existed user/group permissions
        exited = items.get('existed', [])
        perm_data = items.pop('data')
        # Upper data id when type == 'users'
        items_data = [item.upper() for item in perm_data if item is not None] if items['type'] == 'users' else perm_data
        # Remove Updating Restrict users/groups
        if exited and len(exited) > 0:
            # Return users/groups that would be removed permissions
            items['existed'] = list(set(exited) - set(items_data))
            for item_data in items['existed']:
                if items['type'] == 'users':
                    update_user_perm(item_data, perms, items, allow, exited)
                else:
                    update_group_perm(item_data, perms, items, allow, exited)
        # Looping data update
        if len(perm_data) > 0:
            for item_data in perm_data:
                if items['type'] == 'users':
                    update_user_perm(item_data, perms, items, allow, exited)
                else:
                    update_group_perm(item_data, perms, items, allow, exited)


def update_user_perm(item_data, perms, items, allow, exited):
    # Try to get User
    is_phone, phone_number = phone_validate(item_data)
    if is_phone:
        try:
            phone = PhoneNumber.objects.get(phone_number=phone_number)
            user = phone.user
        except models.ObjectDoesNotExist:
            field = 'allow' if allow else 'restrict'
            raise serializers.ValidationError({'message': f'Field error at "{field}_{items["type"]}"'})
    else:
        try:
            user = User.objects.get(id=item_data.upper())
        # Return errors with fields error
        except models.ObjectDoesNotExist:
            field = 'allow' if allow else 'restrict'
            raise serializers.ValidationError(
                {'message': f'Field error at "{field}_{items["type"]}" - some items not exists'})
    hide_users = items.get('hide', None)
    read_only = items.get('read_only', None)
    print(f"Read only: {read_only} | Hide: {hide_users}")
    # Looping handle with permissions
    for perm in perms:
        if read_only:
            if user.id in read_only or user.id.lower() in read_only:
                if perm.split('_')[0] == perm_actions['view']:
                    app_log.info(f"|__ Add READ ONLY permissions for user '{user.id}' - '{perm}'")
                    user.perm_user.add(perm, through_defaults={'allow': allow})
        if hide_users:
            if user.id in hide_users or user.id.lower() in hide_users:
                if perm.split('_')[0] == perm_actions['view']:
                    continue

        is_perm = user.is_perm(perm)
        # Remove when permission is existed and User not in Updated list
        if exited is not None and is_perm and user.id in items['existed']:
            app_log.info(f"|__ Remove permissions user '{user.id}' - '{perm}'")
            user.perm_user.remove(perm)
        elif is_perm:
            app_log.info(f"|__ Continue user '{user.id}' - '{perm}'")
            continue
        # Adding permissions to user
        else:
            app_log.info(f"|__ Add permissions for user '{user.id}' - '{perm}'")
            user.perm_user.add(perm, through_defaults={'allow': allow})


def update_group_perm(item_data, perms, items, allow, exited):
    # Try to get Group
    try:
        group = GroupPerm.objects.get(name=item_data)
    # Return errors with fields error
    except models.ObjectDoesNotExist:
        field = 'allow' if allow else 'restrict'
        raise serializers.ValidationError({'message': f'Field error at "{field}_{items["type"]}"'})
    hide_group = items.get('hide', None)
    read_only = items.get('read_only', None)
    if group is None:
        return
    print(f"Read only: {read_only} | Hide: {hide_group}")
    # Looping handle with permissions
    for perm in perms:
        if read_only:
            if group.name in read_only or group.name.lower() in read_only:
                if perm.split('_')[0] == perm_actions['view']:
                    app_log.info(f"|__ Add READ ONLY permissions for user '{group.name}' - '{perm}'")
                    group.perm.add(perm, through_defaults={'allow': allow})
        if hide_group:
            if group.name in hide_group:
                if perm.split('_')[0] == perm_actions['view']:
                    continue
        group_perm = group.perm.filter(name=perm)
        is_perm = group_perm.exists() and group.perm_group.filter(perm_id=perm, allow=allow).exists()
        # Remove when permission is existed and Group not in Updated list
        if exited is not None and is_perm and group.name in items['existed']:
            app_log.info(f"|__ Remove permissions group '{group.name}' - '{perm}'")
            group.perm.remove(perm)
        elif is_perm:
            app_log.info(f"|__ Continue group '{group.name}' - '{perm}'")
            continue
        # Adding permissions to group
        else:
            app_log.info(f"|__ Add permissions for group '{group.name}' - '{perm}'")
            group.perm.add(perm, through_defaults={'allow': allow})


def list_user_has_perm(perms: list, allow: bool):
    user_perms = UserPerm.objects.filter(
        Q(perm__name__in=perms,
          user__is_superuser=False,
          allow=allow)
    ).distinct('user')
    # Create user_id list in which user has perm
    existed_user = []
    for user in user_perms:
        existed_user.append(user.user.id)
    return existed_user


def list_group_has_perm(perms: list, allow: bool):
    # Get groups has perm
    group_perms = GroupPerm.objects.filter(Q(perm__name__in=perms, allow=allow)).exclude(name=admin_role).distinct()
    # Create group name list in which group has perm
    existed_group = []
    for group in group_perms:
        existed_group.append(group.name)
    return existed_group


def create_full_perm(model, _id=None, user_actions=None):
    content = ContentType.objects.get_for_model(model)
    user_actions = user_actions or []
    # Generate string perm name
    actions = perm_actions.get('full')
    perm_name = f'{content.app_label}_{content.model}'
    if _id is not None:
        perm_name = f'{perm_name}_{_id}'
    list_perm = list()
    # Processing create perm
    for action in actions:
        _perm_name = f"{action}_{perm_name}"
        Perm.objects.get_or_create(
            name=_perm_name,
            note=f"{action.capitalize()} {content.model} - {_id}",
            object_id=str(_id),
            content_type=content
        )
        print(f"Adding permission: {_perm_name}")
        # Add perm to list_perm for register user/nhom
        if action in user_actions:
            print(f"Adding permission for users: {_perm_name}")
            list_perm.append(_perm_name)
    return list_perm

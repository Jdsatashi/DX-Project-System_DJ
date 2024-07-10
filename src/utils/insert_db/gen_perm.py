from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from pyodbc import IntegrityError

from account.models import User, Perm
from utils.constants import acquy
from utils.insert_db.default_roles_perms import set_user_perm


def user_perm():
    users = User.objects.all()
    for user in users:
        # set_user_perm(user, True)

        content_type = ContentType.objects.get_for_model(user)
        perm_name = f'{content_type.app_label}_{content_type.model}_{user.id}'
        tasks = acquy['full']
        for task in tasks:
            perm_name_ = f'{task}_{perm_name}'
            print(f"__Adding permission: {perm_name}")
            try:
                perm_, _ = Perm.objects.get_or_create(
                    name=perm_name_,
                    defaults={'note': f'{task.capitalize()} {content_type.model}',
                              'content_type': content_type, 'object_id': user.id})
                if task != 'destroy':
                    user.perm_user.add(perm_, through_defaults={'allow': True})
            except IntegrityError:
                continue


def add_permissions_for_nvtt_users():
    nvtt_users = User.objects.filter(group_user__name='nvtt')
    for nvtt_user in nvtt_users:
        managed_users = User.objects.filter(clientprofile__nvtt_id=nvtt_user.id)
        add_permissions(nvtt_user, managed_users)


def add_permissions_for_npp_users():
    npp_users = User.objects.filter(Q(clientprofile__is_npp=True) | Q(group_user__name='npp'))
    for npp_user in npp_users:
        managed_users = User.objects.filter(clientprofile__client_lv1_id=npp_user.id)
        add_permissions(npp_user, managed_users)


def add_permissions(user_instance, managed_users):
    content_type = ContentType.objects.get_for_model(User)
    perm_name_list = f'list_{content_type.app_label}_{content_type.model}'
    perm_name_retrieve = f'retrieve_{content_type.app_label}_{content_type.model}'

    for managed_user in managed_users:
        print(f"Handle user: {managed_user}")
        perm_name_list = f"{perm_name_list}_{managed_user.id}"
        perm_name_retrieve = f"{perm_name_retrieve}_{managed_user.id}"
        perm_list = Perm.objects.get_or_create(
            name=perm_name_list,
            defaults={'content_type': content_type,
                      'object_id': managed_user.id}
        )
        perm_retrieve = Perm.objects.get_or_create(
            name=perm_name_retrieve,
            defaults={'content_type': content_type,
                      'object_id': managed_user.id}
        )

        user_instance.perm_user.add(perm_list, perm_retrieve)

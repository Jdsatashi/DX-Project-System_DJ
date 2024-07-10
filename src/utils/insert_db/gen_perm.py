from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from account.models import User, Perm
from utils.insert_db.default_roles_perms import set_user_perm


def user_perm():
    users = User.objects.all()
    for user in users:
        set_user_perm(user, True)


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
        perm_list, created = Perm.objects.get_or_create(
            codename=perm_name_list,
            name=f'Can list {content_type.app_label} {content_type.model} {managed_user.id}',
            content_type=content_type
        )
        perm_retrieve, created = Perm.objects.get_or_create(
            codename=perm_name_retrieve,
            name=f'Can retrieve {content_type.app_label} {content_type.model} {managed_user.id}',
            content_type=content_type
        )

        user_instance.perm_user.add(perm_list, perm_retrieve)
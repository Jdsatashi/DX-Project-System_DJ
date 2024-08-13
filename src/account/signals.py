from django.db import transaction
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from account.models import User, UserGroupPerm, GroupPerm, UserPerm, GrantAccess
from account.queries import get_all_user_perms_sql
from app.logs import app_log
from utils.insert_db.default_roles_perms import set_user_perm


# @receiver(post_save, sender=Perm)
# def add_quyen_to_superuser(sender, instance, created, **kwargs):
#     if created:
#         admin_group, _ = GroupPerm.objects.get_or_create(name=admin_role)
#         admin_group.perm.add(instance, through_defaults={'allow': True})


@receiver(post_save, sender=UserGroupPerm)
def update_group_perm_on_usergroupperm_change(sender, instance, **kwargs):
    # Đảm bảo không gây ra lỗi update vòng lặp
    if hasattr(instance, '_updating'):
        return
    with transaction.atomic():
        # Cập nhật GroupPerm
        group_perm = instance.group
        if group_perm.allow != instance.allow:
            group_perm._updating = True
            group_perm.allow = instance.allow
            group_perm.save()
            del group_perm._updating


@receiver(post_save, sender=GroupPerm)
def update_usergroupperm_on_groupperm_change(sender, instance, **kwargs):
    app_log.info("Signal triggered GroupPerm.")
    if hasattr(instance, '_updating'):
        return
    with transaction.atomic():
        # Cập nhật tất cả các UserGroupPerm liên quan
        user_group_perms = UserGroupPerm.objects.filter(group=instance)
        for user_group_perm in user_group_perms:
            if user_group_perm.allow != instance.allow:
                user_group_perm._updating = True
                user_group_perm.allow = instance.allow
                user_group_perm.save()
                del user_group_perm._updating


@receiver(post_save, sender=User)
def create_user_permissions(sender, instance, created, **kwargs):
    if created:
        set_user_perm(instance, True)


@receiver(m2m_changed, sender=User.perm_user.through)
def handle_user_perm_change(sender, instance, action, reverse, model, pk_set, **kwargs):
    update_grant_access(instance)


def update_grant_access(user):
    access_users = GrantAccess.objects.filter(grant_user=user, active=True)
    if access_users.exists():
        print(f"__ Updating new perm for manager - {user.id}")
        handle_grant_perm(access_users.first())


def handle_grant_perm(grant_user_obj):
    # Get current grant_user perms
    user_current_perms = get_all_user_perms_sql(grant_user_obj.grant_user.id)
    # Get newest grant_user perms
    user_perms = grant_user_obj.grant_user.perm_user.all()
    # Get grant perms of manager
    rent_perm = grant_user_obj.grant_perms.all()
    # Get current manager perms
    current_perm = get_all_user_perms_sql(grant_user_obj.manager.id)
    # Get origin manager perms
    before_manage_perm = list(set(current_perm) - set(rent_perm))
    # Get new perm for adding
    new_perm = set(user_perms) - set(user_current_perms)
    # Get difference perm for removing
    remove_perm = set(user_current_perms) - set(user_perms) - set(before_manage_perm)
    # Looping to add perms
    for perm in new_perm:
        # print(f"Adding: {perm} for manager {grant_user_obj.manager}")
        grant_user_obj.grant_perms.add(perm)
        perm_obj = grant_user_obj.grant_user.userperm_set.get(perm=perm)
        grant_user_obj.manager.perm_user.add(perm, through_defaults={'allow': perm_obj.allow})
    for perm in remove_perm:
        # print(f"Adding: {perm} for manager {grant_user_obj.manager}")
        grant_user_obj.grant_perms.remove(perm)
        # Error when use 'perm_user.remove(perm)'
        UserPerm.objects.filter(perm=perm, user=grant_user_obj.manager).delete()
        # grant_user_obj.manager.perm_user.remove(perm)

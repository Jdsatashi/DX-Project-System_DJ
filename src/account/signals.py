from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from account.models import Perm, User, UserGroupPerm, GroupPerm
from utils.constants import admin_role


@receiver(post_save, sender=Perm)
def add_quyen_to_superuser(sender, instance, created, **kwargs):
    if created:
        superusers = User.objects.filter(is_superuser=True)

        for user in superusers:
            user.perm_user.add(instance, through_defaults={'allow': True})

        admin_group, _ = GroupPerm.objects.get_or_create(name=admin_role)
        admin_group.perm.add(instance, through_defaults={'allow': True})


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
    # Đảm bảo không gây ra lỗi update vòng lặp
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

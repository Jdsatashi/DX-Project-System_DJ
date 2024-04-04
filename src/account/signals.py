from django.db.models.signals import post_save
from django.dispatch import receiver
from account.models import Quyen, User


@receiver(post_save, sender=Quyen)
def add_quyen_to_superuser(sender, instance, created, **kwargs):
    if created:
        superusers = User.objects.filter(is_superuser=True)

        for user in superusers:
            user.quyenUser.add(instance, through_defaults={'allow': True})

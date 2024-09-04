from django.db import transaction

from account.models import GrantAccess


def inactive_users():
    with transaction.atomic():
        grant_access_list = GrantAccess.objects.filter(allow=True)
        for grant_access in grant_access_list:
            print(f"Handle: {grant_access.grant_user}")
            grant_access.active = False
            grant_access.save()

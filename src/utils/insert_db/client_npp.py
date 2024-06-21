from django.db import transaction
from django.db.models import Q

from account.models import User, GroupPerm
from user_system.client_profile.models import ClientProfile

users_list = [
    "C1AGDNG", "C1AGNSA", "C1AGTUT", "C1AGTVT", "C1CTPTH",
    "C1DNTPC", "C1DNTPL", "C1DTHDU", "C1DTHTR", "C1HGNPH",
    "C1KGVDT", "C1STTVK", "C1TGNTU", "C1TGTVH", "C1TNVLH",
    "CDAGLTH", "CNCTTNO", "C1LAPHU", "C1KGNTT", "C1VLTMT",
    "VHSGPVH"
]


def update_npp(user_list: list):
    client_profile = ClientProfile.objects.filter(client_id__in=user_list)
    for profile in client_profile:
        profile.is_npp = True

    with transaction.atomic():
        ClientProfile.objects.bulk_update(client_profile, ['is_npp'])

    u = User.objects.filter(id__in=user_list)
    npp = GroupPerm.objects.get(name='npp')
    for user in u:
        user.group_user.add(npp, through_defaults={'allow': True})


def update_nvtt():
    queryset = User.objects.filter(
        Q(employeeprofile__position__id='NVTT')
    ).select_related('employeeprofile').prefetch_related('employeeprofile__position').exclude(
        group_user__name='admin').distinct()
    nvtt = GroupPerm.objects.get(name='nvtt')

    for user in queryset:
        user.group_user.add(nvtt, through_defaults={'allow': True})

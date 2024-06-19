from django.db import transaction

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

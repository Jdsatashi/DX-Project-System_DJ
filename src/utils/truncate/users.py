from django.db import transaction

from account.models import GrantAccess, User
from app.settings import PROJECT_DIR
from utils.import_excel import file_data_to_dict


def inactive_users():
    with transaction.atomic():
        grant_access_list = GrantAccess.objects.filter(allow=True)
        for grant_access in grant_access_list:
            print(f"Handle: {grant_access.grant_user}")
            grant_access.active = False
            grant_access.save()


def force_update_user():
    file = PROJECT_DIR / 'test' / 'update_users.xlsx'
    mapping = {
        'maKH': 'user_id',
        'tenKH': 'register_name',
        'npp': 'npp',
        'nvtt': 'nvtt',
        'sdt1': 'phone_1',
        'sdt2': 'phone_2',
        'sdt3': 'phone_3',
        'sdtChinh': 'main_phone',
    }
    datas = file_data_to_dict(file, mapping)
    success = list()
    errors = list()
    nvtt_list = {data['nvtt'] for data in datas}
    npp_list = {data['npp'] for data in datas}
    lista = list()
    for nvtt_name in nvtt_list:
        nvtt_user = User.objects.filter(employeeprofile__register_name__icontains=nvtt_name)
        if nvtt_user.exists():
            lista.append(nvtt_user)
    npp_user = User.objects.filter(clientprofile__register_name__in=npp_list, clientprofile__is_npp=True)
    for user_data in datas:
        try:
            pass
        except Exception as e:
            raise e
    print(f"Test nvtt: {len(nvtt_list)} - {len(lista)}")
    print(f"Test npp: {len(npp_list)} - {len(npp_user)}")
    a = npp_list.copy()
    for npp in npp_user:
        print(f"{npp.id} - {npp.clientprofile.register_name}")
        a.remove(npp.clientprofile.register_name)
    print(a)
# from utils.truncate.users import force_update_user

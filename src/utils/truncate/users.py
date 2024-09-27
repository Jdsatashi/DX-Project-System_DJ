import re
import regex

import numpy as np
import pandas as pd
from django.db import transaction
from django.db.models import F, Q
from rest_framework.exceptions import ValidationError

from account.models import GrantAccess, User, PhoneNumber
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

    datas = file_data_to_dict2(file)
    success = list()
    errors = list()
    npp_list = {data['npp'] for data in datas}

    npp_user = User.objects.filter(
        clientprofile__register_name__in=npp_list, clientprofile__is_npp=True
    ).annotate(name=F('clientprofile__register_name')).values_list('name', 'id')
    npp_user_dict = dict(npp_user)
    for user_data in datas:
        if user_data['user_id'] == 'KG040':
            for key, value in user_data.items():
                print(f"{key}: {value} - {type(value)}")
        try:
            with transaction.atomic():
                print(f"Update user id: {user_data['user_id']}")
                success_data = {
                    'line': user_data.get('line_number')
                }
                user = User.objects.get(id=user_data['user_id'])
                profile = user.clientprofile if user.clientprofile else user.create_profile()
                profile.client_lv1_id = npp_user_dict[user_data.get('npp')]
                profile.nvtt_id = user_data.get('nvtt')
                success_data['profile'] = 'updated'
                # Get phone data
                main_phone_field = user_data.get('main_phone', None)
                phones = [user_data['phone_1'], user_data['phone_2'], user_data['phone_3']]

                if main_phone_field:
                    main_phone = str(main_phone_field)
                    main_phone_field = main_phone
                    # Deactivate current main phone
                    current_main_phone = user.phone_numbers.filter(type='main').first()
                    if current_main_phone:
                        current_main_phone.type = 'sub'
                        current_main_phone.save()

                    # Query main phone
                    main_phone_q = PhoneNumber.objects.filter(phone_number=main_phone)
                    # Handle create/update main phone
                    if main_phone_q.exists():
                        # Update if exist
                        main_phone_obj: PhoneNumber = main_phone_q.first()
                        if not main_phone_obj.user_id == user.id:
                            main_phone_obj.user = user
                        main_phone_obj.type = 'main'
                        main_phone_obj.save(update_fields=['user', 'type'])
                        success_data['main_phone'] = 'updated'
                    else:
                        # Create if not exist
                        main_phone_obj = PhoneNumber.objects.create(phone_number=main_phone, user=user, type='main')
                        success_data['main_phone'] = 'created'

                # Handle sub phone
                phone_numbers = {phone for phone in phones if phone not in ['', 'nan', None, main_phone_field]}
                for i, phone_number in enumerate(phone_numbers):
                    # Query sub phone
                    phone_obj = PhoneNumber.objects.filter(phone_number=phone_number)
                    if phone_obj.exists():
                        # Update if exist
                        phone_obj = phone_obj.first()
                        if not phone_obj.user_id == user.id:
                            phone_obj.user = user
                        phone_obj.type = 'sub'
                        phone_obj.save(update_fields=['user', 'type'])
                        success_data[f'phone_{i}'] = 'updated'
                    else:
                        phone_obj = PhoneNumber.objects.create(phone_number=phone_number, user=user)
                        success_data[f'phone_{i}'] = 'created'
                success.append(success_data)
        except User.DoesNotExist:
            errors.append({
                'line': user_data.get('line_number'),
                'error': f"not found user {user_data['user_id']}"
            })
            continue
        except Exception as e:
            raise e
    return success, errors


def force_update_user2():
    file = PROJECT_DIR / 'test' / 'update_users2.xlsx'

    datas = file_data_to_dict2(file)
    success = list()
    errors = list()
    npp_list = {data['npp'] for data in datas}
    nvtt_list = {data['nvtt'] for data in datas}
    print(f"Length: nvtt:{len(nvtt_list)} - npp:{len(npp_list)}")
    npp_user = User.objects.filter(
        clientprofile__register_name__in=npp_list, clientprofile__is_npp=True
    ).distinct().annotate(name=F('clientprofile__register_name')).values_list('name', 'id')
    npp_user_dict = dict(npp_user)

    nvtt_user_dict = dict()
    for nvtt_char in nvtt_list:
        print(f"{nvtt_char}")
        lastname, firstname = extract_last_upper_case(nvtt_char)
        query_first_char = Q(employeeprofile__register_name__startswith=lastname[0])
        query_first_name = Q(employeeprofile__register_name__endswith=firstname)
        nvtt = User.objects.filter(Q(query_first_char & query_first_name))
        if nvtt.count() != 1:
            query = create_character_filter(lastname)
            nvtt = User.objects.filter(Q(
                query
                & Q(employeeprofile__register_name__endswith=firstname)
            ))
            if nvtt.count() != 1:
                query = Q()
                for i, char in enumerate(lastname):
                    if i == 0:
                        query &= query_first_char
                    else:
                        query &= Q(employeeprofile__register_name__icontains=char)
                nvtt = User.objects.filter(Q(
                    query
                    & Q(employeeprofile__register_name__endswith=firstname)
                ))
        nvtt = nvtt.first()
        nvtt_user_dict[nvtt_char] = nvtt.id
        # print(nvtt)
    print(f"Length dict: nvtt:{len(nvtt_user_dict)} - npp:{len(npp_user_dict)}")

    for user_data in datas:
        if user_data['user_id'] == 'KG040':
            for key, value in user_data.items():
                print(f"{key}: {value} - {type(value)}")
        try:
            with transaction.atomic():
                print(f"Update user id: {user_data['user_id']}")
                success_data = {
                    'line': user_data.get('line_number')
                }
                user = User.objects.get(id=user_data['user_id'])
                profile = user.clientprofile if user.clientprofile else user.create_profile()
                profile.client_lv1_id = npp_user_dict[user_data.get('npp')]
                profile.nvtt = nvtt_user_dict[user_data.get('nvtt')]
                success_data['profile'] = 'updated'
                # Get phone data
                main_phone_field = user_data.get('main_phone', None)
                phones = [user_data['phone_1'], user_data['phone_2'], user_data['phone_3']]

                if main_phone_field:
                    main_phone = str(main_phone_field)
                    main_phone_field = main_phone
                    # Deactivate current main phone
                    current_main_phone = user.phone_numbers.filter(type='main').first()
                    if current_main_phone:
                        current_main_phone.type = 'sub'
                        current_main_phone.save()

                    # Query main phone
                    main_phone_q = PhoneNumber.objects.filter(phone_number=main_phone)
                    # Handle create/update main phone
                    if main_phone_q.exists():
                        # Update if exist
                        main_phone_obj: PhoneNumber = main_phone_q.first()
                        if not main_phone_obj.user_id == user.id:
                            main_phone_obj.user = user
                        main_phone_obj.type = 'main'
                        main_phone_obj.save(update_fields=['user', 'type'])
                        success_data['main_phone'] = 'updated'
                    else:
                        # Create if not exist
                        main_phone_obj = PhoneNumber.objects.create(phone_number=main_phone, user=user, type='main')
                        success_data['main_phone'] = 'created'

                # Handle sub phone
                phone_numbers = {phone for phone in phones if phone not in ['', 'nan', None, main_phone_field]}
                for i, phone_number in enumerate(phone_numbers):
                    # Query sub phone
                    phone_obj = PhoneNumber.objects.filter(phone_number=phone_number)
                    if phone_obj.exists():
                        # Update if exist
                        phone_obj = phone_obj.first()
                        if not phone_obj.user_id == user.id:
                            phone_obj.user = user
                        phone_obj.type = 'sub'
                        phone_obj.save(update_fields=['user', 'type'])
                        success_data[f'phone_{i}'] = 'updated'
                    else:
                        phone_obj = PhoneNumber.objects.create(phone_number=phone_number, user=user)
                        success_data[f'phone_{i}'] = 'created'
                success.append(success_data)
        except User.DoesNotExist:
            errors.append({
                'line': user_data.get('line_number'),
                'error': f"not found user {user_data['user_id']}"
            })
            continue
        except Exception as e:
            raise e
    return success, errors


def file_data_to_dict2(file) -> list[dict]:
    column_mapping = {
        'maKH': 'user_id',
        'tenKH': 'register_name',
        'npp': 'npp',
        'nvtt': 'nvtt',
        'sdt1': 'phone_1',
        'sdt2': 'phone_2',
        'sdt3': 'phone_3',
        'sdtChinh': 'main_phone',
    }

    dtype_spec = {
        'sdt1': str,
        'sdt2': str,
        'sdt3': str,
        'sdtChinh': str
    }

    try:
        df = pd.read_excel(file, engine='openpyxl', dtype=dtype_spec)
    except Exception as e:
        raise ValidationError({'message': f'Error reading the Excel file: {str(e)}'})

    missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
    if missing_columns:
        raise ValidationError({'message': f'Missing columns in the file: {", ".join(missing_columns)}'})

    df.rename(columns=column_mapping, inplace=True)
    df['line_number'] = df.index + 2
    df.replace({np.inf: None, -np.inf: None, np.nan: None}, inplace=True)
    data = df.to_dict(orient='records')
    return data


def create_character_filter(query_string):
    # Splits the string into characters
    characters = list(query_string)
    # Creates a Q object for each character and combines them using AND
    query = Q()
    for char in characters:
        query &= Q(employeeprofile__register_name__contains=char)
    return query


def extract_last_upper_case(s):
    # Tìm tất cả các ký tự chữ hoa, bao gồm các ký tự đặc biệt
    matches = regex.findall(r'\p{Lu}', s)
    if not matches:
        return s

    last_upper = matches[-1]
    start_upper = matches[:-1]
    last_upper_index = s.rindex(last_upper)

    remaining = s[last_upper_index + 1:]
    remaining = last_upper + remaining
    print(start_upper, remaining)
    return start_upper, remaining


def is_vietnamese_diacritic(char):
    # Kiểm tra ký tự có nằm trong khoảng các ký tự tiếng Việt có dấu không
    return bool(regex.match(r'\p{Script=Latin}[\u0300\u0301\u0303\u0309\u0323]', char))


# from utils.truncate.users import force_update_user

import time
import time

import dotenv
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import migrations, IntegrityError

from account.models import User
from user_system.client_group.models import ClientGroup
from user_system.client_profile.models import ClientProfile
from user_system.employee_profile.models import Position, EmployeeProfile
from user_system.user_type.models import UserType
from utils.constants import (old_data, maNhomND as farmerID, tenNhomND as farmerGroupName)
from utils.helpers import table_data

dotenv.load_dotenv()


def append_kh(type_kh):
    ctx = {'users': [], 'profiles': []}
    data = table_data(old_data['tb_kh'])
    for k, v in enumerate(data):
        if k == 1:
            print(v)
        client_group_id = ClientGroup.objects.filter(id=v[3]).first()
        code_client_lv1 = v[11] if v[11] != '' else None
        data_profile = {"register_name": v[1], "organization": v[2], "client_group_id": client_group_id,
                        "nvtt_id": v[4], "address": v[7], "client_lv1_id": code_client_lv1, "created_by": v[8]}
        phone = v[5] if v[5] != '' else None
        pw = v[0].lower() if v[10] == '' or v[10] is None else v[10]
        hash_pw = make_password(pw)
        try:
            obj, created = User.objects.get_or_create(id=v[0], defaults={"phone_number": phone, "user_type": type_kh,
                                                                     "password": hash_pw})
        except IntegrityError:
            obj, created = User.objects.get_or_create(id=v[0], defaults={"phone_number": None, "user_type": type_kh,
                                                                         "password": hash_pw})
        if created:
            print(f"User {v[0]} was created successfully.")
        else:
            print(f"User {v[0]} was existed, skipping...")
        obj, created = ClientProfile.objects.get_or_create(client_id=obj, defaults=data_profile)
        if created:
            print(f"User profile {v[0]} was created successfully.")
        else:
            print(f"User profile {v[0]} was existed, skipping...")
    return ctx


def append_nv(type_nv):
    ctx = {'users': [], 'profiles': []}
    data = table_data(old_data['tb_nhanvien'])
    for k, v in enumerate(data):
        if k == 1:
            print(v)
        phone = v[28] if v[28] != '' else None
        email = v[51] if v[51] != '' else None
        pw_hash = make_password(v[0].lower())
        try:
            obj, created = User.objects.get_or_create(
                id=v[0], defaults={'phone_number': phone, 'email': email, 'user_type': type_nv, 'password': pw_hash})
        except IntegrityError:
            obj, created = User.objects.get_or_create(
                id=v[0], defaults={'phone_number': None, 'email': email, 'user_type': type_nv, 'password': pw_hash})
        except ValidationError:
            obj, created = User.objects.get_or_create(
                id=v[0], defaults={'phone_number': None, 'email': email, 'user_type': type_nv, 'password': pw_hash})
        print(obj.id)
        if created:
            print(f"User {v[0]} was created successfully.")
        else:
            print(f"User {v[0]} was existed, skipping...")

        obj, created = EmployeeProfile.objects.get_or_create(employee_id=obj,
                                                             defaults={'fullname': f"{v[2]} {v[3]}", 'gender': v[5]})
        if created:
            print(f"User profile {v[0]} was created successfully.")
        else:
            print(f"User profile {v[0]} was existed, skipping...")
    return ctx


def create_position():
    data = table_data(old_data['tb_chucdanh'])
    for k, v in enumerate(data):
        obj, created = Position.objects.get_or_create(id=v[0], defaults={'name': v[1], 'note': v[2]})
        if created:
            print(f"Created new Position: {v[1]}")
        else:
            print(f"Position {v[1]} already existed, passing...")


def create_client_group_id():
    data = table_data(old_data['tb_nhomKH'])
    for k, v in enumerate(data):
        parentGroup = ClientGroup.objects.filter(id=v[1]).first()

        obj, created = ClientGroup.objects.get_or_create(id=v[0], defaults={'parent_id': parentGroup, 'name': v[2]})
        if created:
            print(f"Created new Group id: {v[2]}")
        else:
            print(f"Group id {v[2]} already existed, passing...")
    obj, created = ClientGroup.objects.get_or_create(id=farmerID, defaults={'name': farmerGroupName})
    if created:
        print(f"Created new Group id: {farmerID}")
    else:
        print(f"Group id {farmerID} already existed, passing...")


def insertDB(apps, schema_editor):
    start_time = time.time()
    type_nv, _ = UserType.objects.get_or_create(user_type="employee")
    type_kh, _ = UserType.objects.get_or_create(user_type="client")
    create_position()
    create_client_group_id()
    append_nv(type_nv)
    append_kh(type_kh)
    print(f"\n__FINISHED__")
    print(f"Complete time: {time.time() - start_time} seconds")


class Migration(migrations.Migration):
    dependencies = [
        ('user_type', '0001_initial'),
        ('account', '0001_initial'),
        ('client_group', '0001_initial'),
        ('client_profile', '0001_initial'),
        ('employee_profile', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insertDB),
    ]

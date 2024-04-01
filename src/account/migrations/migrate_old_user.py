import os
import time
import pyodbc
import dotenv
from django.contrib.auth.hashers import make_password

from account.models import User
from user_system.kh_nhomkh.models import NhomKH
from user_system.kh_profile.models import KHProfile
from user_system.nv_profile.models import NVChucDanh, NVProfile
from user_system.user_type.models import UserType
from utils.constants import (old_data, maNhomND as maNhom, tenNhomND as tenNhom)
from django.db import migrations

dotenv.load_dotenv()


# Connect to MS SQL Server and get data of specific table
def table_data(table_name: str):
    # Get env values
    server = os.environ.get('MSSQL_HOST')
    db_name = os.environ.get('MSSQL_DATABASE')
    user = os.environ.get('MSSQL_USER')
    password = os.environ.get('MSSQL_PASSWORD')
    try:
        connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={db_name};UID={user};PWD={password}'
        con = pyodbc.connect(connection_string)
        cursor = con.cursor()
        query = f'SELECT * FROM {table_name}'
        cursor.execute(query)
        rows = cursor.fetchall()
        con.close()
        return rows
    except pyodbc.Error as e:
        print(f"Error: {e}")
        return None


def append_kh(type_kh):
    ctx = {'users': [], 'profiles': []}
    data = table_data(old_data['tb_kh'])
    for k, v in enumerate(data):
        if k == 1:
            print(v)
        maNhomKH = NhomKH.objects.filter(maNhom=v[3]).first()
        data_profile = {"tenBanKe": v[1], "tenDoanhNghiep": v[2], "maNhomKH": maNhomKH, "maNVTT": v[4], "diaChi": v[7], "nguoiLap": v[8]}
        phone = v[5] if v[5] != '' else None
        pw = v[0].lower() if v[10] == '' else v[10]
        hash_pw = make_password(pw)
        obj, created = User.objects.get_or_create(id=v[0], defaults={"phone_number": phone, "loaiUser": type_kh, "password": hash_pw})
        if created:
            print(f"User {v[0]} was created successfully.")
        else:
            print(f"User {v[0]} was existed, skipping...")
        obj, created = KHProfile.objects.get_or_create(maKH=obj, defaults=data_profile)
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
        obj, created = User.objects.get_or_create(id=v[0], defaults={'phone_number': phone, 'email': email, 'loaiUser': type_nv, 'password': pw_hash})
        print(obj.id)
        if created:
            print(f"User {v[0]} was created successfully.")
        else:
            print(f"User {v[0]} was existed, skipping...")

        obj, created = NVProfile.objects.get_or_create(maNV=obj, defaults={'fullname': f"{v[2]} {v[3]}", 'gioiTinh': v[5]})
        if created:
            print(f"User profile {v[0]} was created successfully.")
        else:
            print(f"User profile {v[0]} was existed, skipping...")
    return ctx


def create_chucdanh():
    data = table_data(old_data['tb_chucdanh'])
    for k, v in enumerate(data):
        obj, created = NVChucDanh.objects.get_or_create(maChucDanh=v[0], defaults={'tenChucDanh': v[1], 'moTa': v[2]})
        if created:
            print(f"Created new chucDanh: {v[1]}")
        else:
            print(f"ChucDanh {v[1]} already existed, passing...")


def create_maNhomKH():
    data = table_data(old_data['tb_nhomKH'])
    for k, v in enumerate(data):
        parentGroup = NhomKH.objects.filter(maNhom=v[1]).first()

        obj, created = NhomKH.objects.get_or_create(maNhom=v[0], defaults={'maNhomCha': parentGroup, 'tenNhom': v[2]})
        if created:
            print(f"Created new maNhom: {v[2]}")
        else:
            print(f"maNhom {v[2]} already existed, passing...")
    obj, created = NhomKH.objects.get_or_create(maNhom=maNhom, defaults={'tenNhom': tenNhom})
    if created:
        print(f"Created new maNhom: {maNhom}")
    else:
        print(f"maNhom {maNhom} already existed, passing...")


def insertDB(apps, schema_editor):
    start_time = time.time()
    type_nv, _ = UserType.objects.get_or_create(loaiUser="nhanvien")
    type_kh, _ = UserType.objects.get_or_create(loaiUser="khachhang")
    create_chucdanh()
    create_maNhomKH()
    append_nv(type_nv)
    append_kh(type_kh)
    print(f"\n__FINISHED__")
    print(f"Complete time: {time.time() - start_time} seconds")


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('user_type', '0001_initial'),
        ('account', '0001_initial'),
        ('kh_nhomkh', '0001_initial'),
        ('kh_profile', '0001_initial'),
        ('nv_profile', '0001_initial'),
        ('account', 'migrate_perm')
    ]

    operations = [
        migrations.RunPython(insertDB),
    ]

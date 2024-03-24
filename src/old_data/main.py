import os
from configparser import ConfigParser
import psycopg2
import pyodbc
import dotenv
from django.contrib.auth.hashers import make_password

from account.models import User
from user_system.kh_nhomkh.models import NhomKH
from user_system.kh_profile.models import KHProfile
from user_system.nv_profile.models import NVChucDanh, NVProfile
from utils.constants import old_data, type_kh, type_nv, maNhomND as maNhom, tenNhomND as tenNhom

dotenv.load_dotenv()

# Get env values
server = os.environ.get('MSSQL_HOST')
db_name = os.environ.get('MSSQL_DATABASE')
user = os.environ.get('MSSQL_USER')
password = os.environ.get('MSSQL_PASSWORD')


# Configuration to connect PostgreSQL
def load_config(filename='postgresql.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to postgresql
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(
            'Section {0} not found in the {1} file'.format(section, filename))
    return config


# Connect to PostgreSQL
def connect_pgs():
    config = load_config()
    """ Connect to the PostgreSQL database server """
    try:
        # connecting to the PostgreSQL server
        with psycopg2.connect(**config) as conn:
            print('Connected to the PostgreSQL server.')
            return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)


# Connect to MS SQL Server and get data of specific table
def table_data(table_name: str):
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


def append_kh():
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
        data_user = {"usercode": v[0], "phone_number": phone, "loaiUser": type_kh, "password": hash_pw}
        obj, created = User.objects.get_or_create(usercode=v[0], defaults={"phone_number": phone, "loaiUser": type_kh, "password": hash_pw})
        if created:
            print(f"User {v[0]} was created successfully.")
        else:
            print(f"User {v[0]} was existed, skipping...")
        obj, created = KHProfile.objects.get_or_create(maKH=obj, defaults=data_profile)
        if created:
            print(f"User profile {v[0]} was created successfully.")
        else:
            print(f"User profile {v[0]} was existed, skipping...")
        ctx['users'].append(data_user)
        ctx['profiles'].append(data_profile)
        print(data_profile)
    return ctx


def append_nv():
    ctx = {'users': [], 'profiles': []}
    data = table_data(old_data['tb_nhanvien'])
    for k, v in enumerate(data):
        if k == 1:
            print(v)
        data_profile = {'maNV': v[0], 'name': f"{v[2]} {v[3]}", 'gender': v[5]}
        phone = v[28] if v[28] != '' else None
        email = v[51] if v[51] != '' else None
        pw_hash = make_password(v[0].lower())
        data_user = {'': v[0], 'phone_number': phone, 'email': email, 'loaiUser': type_nv, 'password': pw_hash}
        obj, created = User.objects.get_or_create(usercode=v[0], defaults={'phone_number': phone, 'email': email, 'loaiUser': type_nv, 'password': pw_hash})
        print(obj.usercode)
        if created:
            print(f"User {v[0]} was created successfully.")
        else:
            print(f"User {v[0]} was existed, skipping...")

        obj, created = NVProfile.objects.get_or_create(maNV=obj, defaults={'fullname': f"{v[2]} {v[3]}", 'gioiTinh': v[5]})
        if created:
            print(f"User profile {v[0]} was created successfully.")
        else:
            print(f"User profile {v[0]} was existed, skipping...")
        ctx['users'].append(data_user)
        ctx['profiles'].append(data_profile)
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

import os
from datetime import datetime

import pyodbc
import dotenv
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from rest_framework import serializers

from account.models import User
from .constants import *

dotenv.load_dotenv()


def value_or_none(value, condition, _return):
    return value if value != condition else _return


# Connect to MS SQL Server and get data of specific table
def table_data(table_name: str):
    # Get env values
    server = os.environ.get('MSSQL_HOST')
    db_name = os.environ.get('MSSQL_DATABASE')
    user = os.environ.get('MSSQL_USER')
    password = os.environ.get('MSSQL_PASSWORD')
    drivers = ["SQL Server", "ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]
    for i, driver in enumerate(drivers):
        try:
            connection_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={user};PWD={password}"
            if i >= 1:
                connection_string += ";TrustServerCertificate=yes"
            print(f"Attempting to connect using driver: {driver}")
            print(f"Connection string: {connection_string}")
            con = pyodbc.connect(connection_string)
            cursor = con.cursor()
            query = f"SELECT * FROM {table_name}"
            cursor.execute(query)
            rows = cursor.fetchall()
            con.close()
            return rows
        except pyodbc.Error as e:
            print(f"Error with driver '{driver}': {e}")
    return None


def generate_id(ma_nhom):
    # Get last 2 number of year (2024 => get '24')
    current_year = str(datetime.now().year)[-2:]
    if ma_nhom == maNhomND:
        code = 'ND'
    else:
        return None
    id_template = f'{code}{current_year}'

    existing_ids = User.objects.filter(id__startswith=id_template).values_list('id', flat=True)

    if not existing_ids:
        new_id = f'{id_template}0001'
    else:
        last_id = max(existing_ids)
        last_sequence_number = int(last_id[-4:])
        new_sequence_number = last_sequence_number + 1

        new_id = f'{id_template}{new_sequence_number:04d}'

    return new_id


def phone_validate(phone):
    """
    Validate phone number
    """
    if phone is None or phone == '':
        raise serializers.ValidationError({'phone_number': ['Bạn phải nhập số điện thoại.']})
    if phone.startswith('0'):
        phone = phone[1:]
    if ' ' in phone:
        raise serializers.ValidationError({'phone_number': ['Số điện thoại bắt buộc không có khoảng trắng.']})

    phone_regex = RegexValidator(
        regex=r'^\d{9,}$',
        message="Số điện thoại phải được nhập ở định dạng: '+999999999'. Tối đa 15 chữ số."
    )
    try:
        phone_regex(phone)
        print(f"Phone valid")
        return True, phone
    except ValidationError:
        print(f"Phone error")
        return False, phone


if __name__ == '__main__':
    print(f"Test database")
    if table_data(old_data['tb_congty']) is not None:
        print(f"Connect ok!")
    print(f"Fail to connect")

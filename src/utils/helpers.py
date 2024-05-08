import random
import pyodbc
import unicodedata
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from rest_framework import serializers

from account.models import User
from utils.env import OLD_SQL_HOST, OLD_SQL_DB, OLD_SQL_USER, OLD_SQL_PW
from .constants import *


def value_or_none(value, condition, _return):
    return value if value != condition else _return


# Connect to MS SQL Server and get data of specific table
def table_data(table_name: str, amount='*', options=None):
    # Get env values
    server = OLD_SQL_HOST
    db_name = OLD_SQL_DB
    user = OLD_SQL_USER
    password = OLD_SQL_PW
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
            print(f"\nOptions = {options}")
            if options is None:
                query = f"SELECT {amount} FROM {table_name}"
            else:
                print(f"Query options")
                query = f"""
                SELECT *
                FROM {table_name}
                ORDER BY [idChiTiet]
                OFFSET {options.get('start')} ROWS
                FETCH NEXT {options.get('end')} ROWS ONLY;
                """

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
    origin_phone = phone
    if phone is None or phone == '':
        raise serializers.ValidationError({'phone_number': ['Bạn phải nhập số điện thoại.']})
    if phone.startswith('0'):
        phone = phone[1:]
    if ' ' in phone:
        raise serializers.ValidationError({'phone_number': ['Số điện thoại bắt buộc không có khoảng trắng.']})

    phone_regex = RegexValidator(
        regex=r'^\d{9,}$',
        message="Số điện thoại phải được nhập ở định dạng: '999999999'. Tối đa 15 chữ số."
    )
    try:
        phone_regex(phone)
        print(f"Phone valid")
        return True, origin_phone
    except ValidationError:
        print(f"Phone error")
        return False, origin_phone


def generate_digits_code():
    list_digit = generate_digits(6)
    random_digit_string = ''.join(map(str, list_digit))
    return random_digit_string


def generate_digits(amount: int):
    selected_digits = list()
    for i in range(amount):
        digits = list(range(10))
        random.shuffle(digits)
        selected_digits.append(digits[:1][0])
    if len(set(selected_digits)) <= 1:
        return generate_digits(amount)
    return selected_digits


def normalize_vietnamese(text):
    # Remove Vietnamese characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')
    # Replace ' ' space to '_' dash
    text = text.replace(' ', '_').lower()
    return text


def get_content(model):
    return ContentType.objects.get_for_model(model)


if __name__ == '__main__':
    print(f"Test database")
    if table_data(old_data['tb_congty']) is not None:
        print(f"Connect ok!")
    print(f"Fail to connect")

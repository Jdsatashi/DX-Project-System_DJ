import datetime
import os

import pandas as pd

from account.models import User
from app.settings import PROJECT_DIR
from marketing.order.api.serializers import update_point, update_season_stats_user
from marketing.order.models import create_or_get_sale_stats_user


def remove_user_orders(user_id: str):
    user = User.objects.filter(id=user_id).first()
    if user is None:
        return "not found user"
    # Delete orders
    user.order_set.all().delete()
    return "success"


def update_order_from_excel(user_id: str):
    user = User.objects.filter(id=user_id).first()
    if user is None:
        return "not found user"


def get_all_kh():
    file_path = os.path.join(PROJECT_DIR, 'update', 'updateUserStats.xlsx')
    today = datetime.datetime.today().date()
    first_date = today.replace(day=1)

    # Đọc file Excel
    df = pd.read_excel(file_path, engine='openpyxl')

    # Lấy toàn bộ dữ liệu từ cột 'ma_khach_hang'
    ma_khach_hang_data = df['ma_khach_hang'].tolist()

    users = User.objects.filter(id__in=ma_khach_hang_data)

    for user in users:
        update_point(user)
        update_season_stats_user(user, first_date)
        create_or_get_sale_stats_user(user, first_date)

    # Hiển thị dữ liệu
    print(ma_khach_hang_data)

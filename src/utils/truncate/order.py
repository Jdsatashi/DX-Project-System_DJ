import datetime
import os

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum

from account.models import User
from app.settings import PROJECT_DIR
from marketing.order.api.serializers import update_point, update_season_stats_user
from marketing.order.models import create_or_get_sale_stats_user, Order, OrderDetail
from marketing.sale_statistic.models import UserSaleStatistic, SaleTarget, UsedTurnover
from system_func.models import PeriodSeason
from utils.constants import so_type


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
    last_date = (first_date + relativedelta(months=1)) - datetime.timedelta(days=1)

    last_date_last_month = first_date - datetime.timedelta(days=1)

    first_date_last_month = last_date_last_month.replace(day=1)
    # Đọc file Excel
    df = pd.read_excel(file_path, engine='openpyxl')

    # Lấy toàn bộ dữ liệu từ cột 'ma_khach_hang'
    ma_khach_hang_data = df['ma_khach_hang'].tolist()

    users = User.objects.filter(id__in=ma_khach_hang_data)

    #for user in users:
    #     update_point(user)
    #     update_season_stats_user(user, first_date_last_month)
    #    create_or_get_sale_stats_user(user, first_date_last_month)
    #
    #for user in users:
    #     update_point(user)
    #     update_season_stats_user(user, first_date)
    #    create_or_get_sale_stats_user(user, first_date)

    for user in users:
        user_stats, _ = UserSaleStatistic.objects.get_or_create(user=user)

        query_filter = Q(client_id=user) & Q(date_get__range=(first_date, last_date))

        filter_so_count = Q(Q(query_filter) & Q(
            Q(new_special_offer__count_turnover=True) | Q(new_special_offer__type_list=so_type.consider_user)
            | Q(new_special_offer__isnull=True)
        ))

        exclude_so = Q(Q(status='deactivate') |
                       Q(id_so__isnull=False) | Q(id_offer_consider__isnull=False))

        orders_count = Order.objects.filter(filter_so_count).exclude(exclude_so)

        orders_so = (Order.objects.filter(query_filter & Q(Q(is_so=True))).exclude(
            new_special_offer__type_list=so_type.consider_user))

        total_used = 0
        sale_target, _ = SaleTarget.objects.get_or_create(month=first_date)
        for order in orders_so:
            result = OrderDetail.objects.filter(order_id=order).aggregate(total_order_box=Sum('order_box'))
            total_order_box = result.get('total_order_box', 0) or 0
            if order.new_special_offer:
                target = order.new_special_offer.target if order.new_special_offer.target > 0 else sale_target.month_target
            else:
                target = sale_target.month_target
            total_used += total_order_box * target

        total_turnover = \
            OrderDetail.objects.filter(order_id__in=orders_count).aggregate(total_price=Sum('product_price'))[
                'total_price'] or 0

        print(f"Create user stats: {user_stats}")

        if orders_count.exists():
            user_stats.turnover = total_turnover - total_used
            user_stats.save()
            UsedTurnover.objects.create(user_sale_stats=user_stats, turnover=total_turnover, purpose='admin_fix',
                                        note='tính tự động')
            UsedTurnover.objects.create(user_sale_stats=user_stats, turnover=-abs(total_used), purpose='admin_fix',
                                        note='tính tự động')

    # Hiển thị dữ liệu
    print(ma_khach_hang_data)

# from utils.truncate.order import get_all_kh

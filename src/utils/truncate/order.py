import datetime
import math
import os
import random
import time

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum, Prefetch
from openpyxl import Workbook

from account.models import User
from app.logs import app_log
from app.settings import PROJECT_DIR
from marketing.order.models import Order, OrderDetail
from marketing.price_list.models import PriceList, ProductPrice
from marketing.sale_statistic.models import UserSaleStatistic, SaleTarget, UsedTurnover
from system_func.models import PeriodSeason, PointOfSeason
from user_system.client_profile.models import ClientProfile


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

    # for user in users:
    #     update_point(user)
    #     update_season_stats_user(user, first_date_last_month)
    #    create_or_get_sale_stats_user(user, first_date_last_month)
    #
    # for user in users:
    #     update_point(user)
    #     update_season_stats_user(user, first_date)
    #    create_or_get_sale_stats_user(user, first_date)


def turnover_user(users, first_date, last_date):
    print(f"Total user: {len(users)}")
    for user in users:
        user_stats, _ = UserSaleStatistic.objects.get_or_create(user=user)
        print(f"Date: {first_date} | {last_date}")
        query_filter = Q(client_id=user) & Q(date_get__range=(first_date, last_date))

        filter_so_count = Q(Q(query_filter) & Q(
            Q(new_special_offer__count_turnover=True)
            # | Q(new_special_offer__type_list=so_type.consider_user)
            | Q(new_special_offer__isnull=True)
        ))

        exclude_so = Q(Q(status='deactivate') |
                       Q(id_so__isnull=False) | Q(id_offer_consider__isnull=False))
        orders_count = Order.objects.filter(filter_so_count).exclude(exclude_so)
        print(f"Normal order: {orders_count.count()}")

        orders_so = (Order.objects.filter(query_filter & Q(Q(is_so=True)))
                     # .exclude(new_special_offer__type_list=so_type.consider_user)
                     )
        print(f"So order: {orders_so.count()}")

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

        print(f"User stats: {user_stats.user} - {user_stats}")
        print(f"Total: {total_turnover} | Used: {total_used}")
        if orders_count.exists() or orders_so.exists():
            user_stats.turnover += total_turnover - total_used
            user_stats.save()
            UsedTurnover.objects.create(user_sale_stats=user_stats, turnover=total_turnover, purpose='admin_fix',
                                        note='tính tự động')
            UsedTurnover.objects.create(user_sale_stats=user_stats, turnover=-abs(total_used), purpose='admin_fix',
                                        note='tính tự động')


def delete_new_order():
    orders = Order.objects.filter(id__startswith='MTN').delete()


def get_order_by_npp(start_date, end_date):
    orders = Order.objects.filter(
        date_company_get__gte=start_date,
        date_company_get__lt=end_date
    ).exclude(status='deactivate').prefetch_related(
        Prefetch('client_id__clientprofile')
    )

    # Bước 2 và 3: Lấy danh sách client_profile và lọc theo client_lv1_id
    client_profiles = ClientProfile.objects.filter(
        client_id__in=orders.values_list('client_id', flat=True)
    ).select_related('client_group_id')

    # Bước 4: Nhóm các đơn hàng theo client_lv1_id
    orders_by_client_lv1 = {}
    for profile in client_profiles:
        client_lv1_id = profile.client_lv1_id
        if client_lv1_id:
            if client_lv1_id not in orders_by_client_lv1:
                orders_by_client_lv1[client_lv1_id] = []
            client_orders = orders.filter(client_id=profile.client_id)
            orders_by_client_lv1[client_lv1_id].extend(client_orders)

    # Xử lý trường hợp không có clientprofile hoặc không có client_lv1_id
    orders_no_lv1 = orders.filter(client_id__clientprofile__isnull=True) | orders.filter(
        client_id__clientprofile__client_lv1_id__isnull=True)
    orders_by_client_lv1['no_client_lv1'] = list(orders_no_lv1)


def update_nvtt():
    current_season = PeriodSeason.get_period_by_date('point')
    date_ = current_season.from_date
    orders = Order.objects.filter(Q(date_get__gte=date_) & Q(nvtt_id__isnull=True))

    total_items = orders.count()
    print(f"Total items: {total_items}")
    quantity_loop = 2000
    time_loop = math.ceil(total_items / quantity_loop)

    for i in range(time_loop):
        start_items = i * quantity_loop
        end_items = start_items + quantity_loop
        if i == time_loop:
            end_items = total_items % i
        print(f"-- i: {i} | start {start_items} to {end_items}")
        orders_data = orders[start_items:end_items]
        update_orders(orders_data)


def update_orders(orders):
    orders_not_have_client = list()
    client_not_have_profile = list()
    client_not_have_nvtt = list()
    updating_order = list()

    for order in orders:
        user = order.client_id

        if user:
            if user.clientprofile:
                if user.clientprofile.nvtt_id:
                    order.nvtt_id = user.clientprofile.nvtt_id
                    updating_order.append(order)
                else:
                    client_not_have_nvtt.append(order.id)
            else:
                client_not_have_profile.append(order.id)
        else:
            orders_not_have_client.append(order.id)
    print(f"Total update: {len(updating_order)}")
    print(f"Order not have client: {orders_not_have_client}")
    print(f"Client not have profile: {client_not_have_profile}")
    print(f"Client not have nvtt: {client_not_have_nvtt}")

    Order.objects.bulk_update(updating_order, ['nvtt_id'])


def update_user_point():
    current_season: PeriodSeason = PeriodSeason.get_period_by_date('point')
    date_ = current_season.from_date
    date_end = current_season.to_date
    users_with_orders = User.objects.filter(
        order__date_get__gte=date_,
        order__date_get__lte=date_end
    ).distinct()

    points_of_season = PointOfSeason.objects.filter(
        user__in=users_with_orders,
        period=current_season
    )
    print(f"items: {points_of_season.count()}")
    with transaction.atomic():
        update_user = list()
        for point_user in points_of_season:
            point_user.auto_point()
            update_user.append(point_user)
        PointOfSeason.objects.bulk_update(update_user, ['point', 'total_point'])


def update_user_turnover():
    today = datetime.datetime.today()
    current_date = today.date()
    start_month = current_date.replace(day=1)
    end_month = (start_month + relativedelta(months=1)) - datetime.timedelta(days=1)
    users_with_orders = User.objects.filter(
        order__date_get__gte=start_month,
        order__date_get__lt=end_month
    ).distinct()
    turnover_user(users_with_orders, start_month, end_month)


def update_npp_order():
    start_time = time.time()
    app_log.info(f"Start update details")

    orders = (Order.objects.filter(client_id__isnull=False, client_id__clientprofile__isnull=False, npp_id__isnull=True)
              .order_by('-id'))

    total_count = orders.count()

    chunk_size = 2000

    time_loop = math.ceil(total_count / chunk_size)
    for a in range(time_loop):
        start_time_2 = time.time()

        start_item = a * chunk_size
        end_item = start_item + chunk_size
        if end_item > total_count:
            end_item = total_count

        try:
            app_log.info(f"--\nGet data from: {start_item} - {end_item} \n--\n")
            paginator = Paginator(orders, chunk_size)
            page = paginator.page(a + 1)

            process_update_npp(page.object_list)
        except Exception as e:
            app_log.error(f"\nWhen get data from: {start_item} - {end_item}\n")
            raise e

        app_log.info(f"Complete UPDATE ORDER items {start_item} - {end_item}: {time.time() - start_time_2} seconds")

        if end_item == total_count:
            break

    app_log.info(f"Complete UPDATE ORDER time: {time.time() - start_time} seconds")


def delete_order_client_none():
    orders = Order.objects.filter(client_id__isnull=True).order_by('-id')
    id_list = orders.values_list('id', flat=True)
    print(f"Count: {orders.count()}")
    print(f"Orders id: {list(id_list)}")
    # Bước 3: Lưu id_list vào file Excel
    # Tạo một workbook mới
    wb = Workbook()
    ws = wb.active
    ws.title = "Deleted Orders"

    # Thêm tiêu đề
    ws.append(["Order ID"])

    # Thêm các giá trị id vào Excel
    for order_id in id_list:
        ws.append([order_id])

    # Bước 4: Lưu file vào thư mục dự án
    # Lấy đường dẫn thư mục project từ settings
    project_dir = settings.PROJECT_DIR  # Thư mục gốc của dự án

    # Tạo đường dẫn đến file Excel
    random_numbers = [random.randint(1, 10) for _ in range(5)]

    file_path = os.path.join(project_dir, f'deleted_orders_{random_numbers}.xlsx')

    # Lưu file Excel
    wb.save(file_path)
    orders.delete()
    return f"File saved at {file_path}"


def process_update_npp(orders):
    with transaction.atomic():
        list_orders_update = []
        for i, order in enumerate(orders):
            if order.npp_id in [None, '']:
                order.npp_id = order.client_id.clientprofile.client_lv1_id
                app_log.info(f"Test: {order.id} - {order.npp_id}")

                list_orders_update.append(order)
        Order.objects.bulk_update(list_orders_update, ['npp_id'])


def update_amis_point():
    try:
        with transaction.atomic():
            period: PeriodSeason = PeriodSeason.get_period_by_date('point')
            start = '2024-01-02'
            end = '2024-12-09'
            start_date = datetime.datetime.strptime(start, '%Y-%m-%d').date()   # period.from_date
            end_date = datetime.datetime.strptime(end, '%Y-%m-%d').date() # period.to_date
            orders = Order.objects.filter(date_get__range=[start_date, end_date]
                                          )
            order_users = orders.values_list('client_id__id', flat=True)
            order_ids = orders.values_list('id', flat=True)
            main_pl: PriceList = PriceList.get_main_pl()
            products_price = ProductPrice.objects.filter(price_list=main_pl)
            product_price_dict = {item.product_id: item.point for item in products_price}

            orders_detail = OrderDetail.objects.filter(order_id__in=order_ids, point_get=0)

            # list of updated
            update_details = list()
            error_list = list()
            product_unpoint = set()
            success_list = list()
            for i, detail in enumerate(orders_detail):
                product_id = detail.product_id_id
                product_point = product_price_dict.get(product_id, None)
                if product_point is None:
                    error_detail = {
                        'detail_id': detail.id,
                        'order': detail.order_id_id,
                        'product': product_id
                    }
                    product_unpoint.add(product_id)
                    error_list.append(error_detail)
                    continue
                point = product_point
                point_get = detail.order_box * point
                detail.point_get = point_get
                update_details.append(detail)
                success_list.append({'detail_id': detail.id, 'order': detail.order_id_id})
            print(f"Error list: \n{error_list}")
            print(f"product_unpoint: \n{product_unpoint}")
            print(f"Test main price list: {main_pl.id} - {main_pl.name}")
            print(f"Result: \n - Updated: {len(update_details)}\n - Failed: {len(error_list)}")
            print(f"User: {order_users.distinct().count()} \n{set(order_users)}")
            # raise ValueError('break for testing')
            OrderDetail.objects.bulk_update(update_details, ['point_get'])

            points_of_season = PointOfSeason.objects.filter(
                user__in=set(order_users),
                period=period
            )
            print(f"items: {points_of_season.count()}")
            with transaction.atomic():
                update_user = list()
                for point_user in points_of_season:
                    point_user.auto_point()
                    update_user.append(point_user)
                PointOfSeason.objects.bulk_update(update_user, ['point', 'total_point'])

    except Exception as e:
        raise e
# from utils.truncate.order import get_all_kh

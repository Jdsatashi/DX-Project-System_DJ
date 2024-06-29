import json
import math
import time

from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef
from django.utils.timezone import make_aware

from account.models import User, GroupPerm
from app.logs import app_log
from marketing.company.models import Company
from marketing.order.models import Order, OrderDetail, OrderBackup, OrderBackupDetail
from marketing.price_list.models import PriceList, ProductPrice, SpecialOffer, SpecialOfferProduct
from marketing.product.models import Product, UseObject, UseFor, ProductCategory, CategoryDetail, RegistrationCert, \
    Producer, RegistrationUnit, ProductType
from user_system.client_profile.models import ClientProfile, ClientGroup
from user_system.employee_profile.models import EmployeeProfile, Position, Department
from utils.helpers import table_data, normalize_vietnamese, table_data_2, count_table_items
from utils.constants import (old_data, maNhomND as farmerID, tenNhomND as farmerGroupName)


def append_kh():
    type_kh = "client"
    ctx = {'users': [], 'profiles': []}
    data = table_data(old_data['tb_kh'])
    for k, v in enumerate(data):
        if k == 1:
            app_log.info(v)
        client_group_id = ClientGroup.objects.filter(id=v[3]).first()
        group_client = GroupPerm.objects.get(name='client')
        group_of_user = GroupPerm.objects.filter(display_name__icontains=client_group_id.name).first()
        code_client_lv1 = v[11] if v[11] != '' else None
        data_profile = {"register_name": v[1], "organization": v[2], "client_group_id": client_group_id,
                        "nvtt_id": v[4], "address": v[7], "client_lv1_id": code_client_lv1, "created_by": v[8]}
        created_time = make_aware(v[8])
        phone = v[5] if v[5] != '' else None
        pw = v[0].lower() if v[10] == '' or v[10] is None else v[10]
        hash_pw = make_password(pw)
        user, created = User.objects.get_or_create(id=v[0], defaults={"user_type": type_kh,
                                                                      "password": hash_pw})
        user.created_at = created_time
        user.save()
        user.group_user.add(group_client, through_defaults={'allow': True})
        try:
            if phone is not None and len(phone) <= 24:
                user.phone_numbers.get_or_create(phone_number=phone)
        except IntegrityError:
            pass

        if created:
            app_log.info(f"User {v[0]} was created successfully.")
        else:
            app_log.info(f"User {v[0]} was existed, skipping...")
        obj, created = ClientProfile.objects.get_or_create(client_id=user, defaults=data_profile)
        if created:
            app_log.info(f"User profile {v[0]} was created successfully.")
            obj.created_at = created_time
            obj.save()
        else:
            app_log.info(f"User profile {v[0]} was existed, skipping...")
        if group_of_user is not None:
            user.group_user.add(group_client, through_defaults={'allow': True})
    return ctx


def append_nv():
    type_nv = "employee"
    ctx = {'users': [], 'profiles': []}
    data = table_data(old_data['tb_nhanvien'])
    for k, v in enumerate(data):
        created_time = make_aware(v[65])
        app_log.info(created_time)
        if k == 1:
            app_log.info(v)
        phone = v[28] if v[28] != '' else None
        email = v[51] if v[51] != '' else None
        pw_hash = make_password(v[0].lower())
        obj, created = User.objects.get_or_create(
            id=v[0], defaults={'email': email, 'user_type': type_nv, 'password': pw_hash})
        obj.created_at = created_time
        obj.save()
        try:
            if phone is not None and len(phone) <= 24:
                obj.phone_numbers.get_or_create(phone_number=phone)
        except IntegrityError:
            pass
        if created:
            app_log.info(f"User {v[0]} was created successfully.")
        else:
            app_log.info(f"User {v[0]} was existed, skipping...")

        obj, created = EmployeeProfile.objects.get_or_create(employee_id=obj,
                                                             defaults={'register_name': f"{v[2]} {v[3]}",
                                                                       'gender': v[5]})
        obj.created_at = created_time
        obj.save()
        if created:
            app_log.info(f"User profile {v[0]} was created successfully.")
        else:
            app_log.info(f"User profile {v[0]} was existed, skipping...")
    add_department()
    add_user_department()
    create_position()
    add_user_position()
    return ctx


def create_position():
    data = table_data(old_data['tb_chucDanh'])
    for k, v in enumerate(data):
        obj, created = Position.objects.get_or_create(id=v[0], defaults={'name': v[1], 'note': v[2]})
        if created:
            app_log.info(f"Created new Position: {v[1]}")
        else:
            app_log.info(f"Position {v[1]} already existed, passing...")


def add_user_position():
    data = table_data(old_data['tb_chucDanhUser'])
    for k, v in enumerate(data):
        app_log.info(f"Test data: {v}")
        user = User.objects.get(id=v[1])
        employee = user.employeeprofile
        position = Position.objects.filter(id=v[2]).first()
        app_log.info(f"Test user: {employee} - {position}")
        try:
            employee.position.add(position)
        except Exception as e:
            raise e
        try:
            nv = GroupPerm.objects.get(name="employee")
            user.group_user.add(nv, through_defaults={'allow': True})
            if v[2] == "NVTT":
                nvtt = GroupPerm.objects.get(name="nvtt")
                user.group_user.add(nvtt, through_defaults={'allow': True})
        except Exception as e:
            raise e


def add_department():
    data = table_data(old_data['tb_phongBan'])
    for k, v in enumerate(data):
        app_log.info(f"Test data full: {v}")
        input_data = {
            'name': v[1],
            'note': v[2]
        }
        try:
            obj, created = Department.objects.get_or_create(id=v[6], defaults=input_data)
        except Exception as e:
            raise e

        app_log.info(f"Test data 2: {obj}")


def add_user_department():
    data = table_data(old_data['tb_phongBanUser'])
    for k, v in enumerate(data):
        app_log.info(f"Test data full: {v}")
        employee = EmployeeProfile.objects.filter(employee_id=v[1]).first()
        department = Department.objects.filter(id=v[3]).first()
        if employee and department:
            app_log.info(f"Added")
            employee.department.add(department)


def create_client_group_id():
    data = table_data(old_data['tb_nhomKH'])
    for k, v in enumerate(data):
        parentGroup = ClientGroup.objects.filter(id=v[1]).first()

        obj, created = ClientGroup.objects.get_or_create(id=v[0], defaults={'parent_id': parentGroup, 'name': v[2]})
        obj.created_at = make_aware(v[4])
        if created:
            app_log.info(f"Created new Group id: {v[2]}")
        else:
            app_log.info(f"Group id {v[2]} already existed, passing...")
    obj, created = ClientGroup.objects.get_or_create(id=farmerID, defaults={'name': farmerGroupName})
    if created:
        app_log.info(f"Created new Group id: {farmerID}")
    else:
        app_log.info(f"Group id {farmerID} already existed, passing...")


# Get old company
def add_old_company(apps, schema_editor):
    data = table_data(old_data['tb_congty'])
    for k, v in enumerate(data):
        try:
            company = Company.objects.create(id=v[0], name=v[1], note=v[2], color_code=v[5])
            app_log.info(f"Added company {v[1]} - {v[0]}")
            company.created_at = make_aware(v[3])
            company.save()
        except Exception as e:
            app_log.info(f"----- ERROR -----")
            app_log.info(f"Message: Error when adding company.")
            app_log.info(e)
            raise Exception(e)


# Adding old Product
def old_product_type():
    data = table_data(old_data['tb_loaiThuoc'])
    app_log.info(f"--------------- ADDING PRODUCT TYPE --------------")
    for i, k in enumerate(data):
        app_log.info(f"Adding product type: {k[1]}")
        _type, _ = ProductType.objects.get_or_create(id=k[0], name=k[1])


def old_product_category():
    data = table_data(old_data['tb_thuoc'])
    app_log.info(f"---------- ADDING PRODUCT CATEGORY ----------")
    for i, v in enumerate(data):
        v = [item.strip() if isinstance(item, str) else item for item in v]
        product_type = ProductType.objects.get(id=v[2])

        unit, _ = RegistrationUnit.objects.get_or_create(unit=v[11], address=v[12])
        producer, _ = Producer.objects.get_or_create(name=v[13], address=v[14])
        registration = {
            'date_activated': v[6],
            'date_expired': v[7],
            'registered_unit': unit,
            'producer': producer
        }
        register_cert, _ = RegistrationCert.objects.get_or_create(id=v[5], defaults=registration)
        company = Company.objects.get(id=v[16])
        insert_data = {
            'name': v[1],
            'product_type': product_type,
            'ingredient': v[8],
            'amount': v[9],
            'poison_group': v[10],
            'registration': register_cert,
            'company': company,
            'amount_warning': int(v[17]),
            'status': 'active' if v[15] == 1 else 'deactivate'
        }
        app_log.info(f"Adding product category: {v[0]} - {v[1]}")
        product_cate, _ = ProductCategory.objects.get_or_create(id=v[0], defaults=insert_data)
        product_cate.created_at = make_aware(v[3])
        product_cate.save()


def old_product():
    data = table_data(old_data['tb_sanpham'])
    app_log.info(f"---------- ADDING PRODUCT ----------")
    try:
        for i, v in enumerate(data):
            insert = {
                'name': v[1],
                'main_id': v[8],
                'created_by': v[6],
            }
            category, note = check_filter(v[7])
            if category is not None:
                insert['category'] = category
                insert['product_type'] = category.product_type
                if note:
                    insert['note'] = json.dumps({"notes": f"Category {v[7]} not found", "category": f"{v[7]}"})
            app_log.info(f"Adding product: {v[0]} - {v[1]}")
            product, _ = Product.objects.get_or_create(id=v[0], defaults=insert)
            product.created_at = make_aware(v[5])
            product.save()
    except Exception as e:
        app_log.info(f"----- ERROR -----")
        app_log.info(f"Message: Error when adding data to product.")
        app_log.info(e)
        raise e


def old_cate_detail():
    data = table_data(old_data['tb_thuocChitiet'])
    norm_vn = normalize_vietnamese
    app_log.info(f"--------------- ADDING CATEGORY DETAIL --------------")
    for i, v in enumerate(data):
        use_on, _ = UseObject.objects.get_or_create(id=norm_vn(v[2]), defaults={'name': v[2]})
        use_for, _ = UseFor.objects.get_or_create(id=norm_vn(v[3]), defaults={'name': v[3]})
        base_id = v[1]
        category = ProductCategory.objects.filter(id=base_id).first()
        insert = {
            'use_object': use_on,
            'use_for': use_for,
            'dosage': v[4],
            'usage': v[5]
        }
        if category is not None:
            insert['cate_id'] = category
        app_log.info(f"Adding category detail: {v[1]}")
        # app_log.info(insert)
        cate_data = CategoryDetail.objects.get_or_create(**insert)


def check_filter(data, i=0):
    i += 1
    note = False
    if i == 0:
        category = ProductCategory.objects.filter(id=data)
    else:
        category = ProductCategory.objects.filter(id__icontains=data)
        note = True
    app_log.info(f"Data: {data}")
    if len(data) <= 1:
        return None, note
    elif not category.exists():
        base_id = data[:-1]
        return check_filter(base_id, i)
    return category.first(), note


# Migrate old Data of Price List
def price_list():
    data = table_data(old_data['tb_bangGia'])
    for k, v in enumerate(data):
        if k == 1:
            app_log.info(v)
            insert = {
                "id": v[0],
                "name": v[1],
                "date_start": v[2],
                "date_end": v[3],
                "created_by": v[8],
                "created_at": v[7]
            }
            app_log.info(insert)
        prl = PriceList.objects.create(id=v[0], name=v[1], date_start=v[2],
                                       date_end=v[3], created_by=v[8])
        prl.created_at = make_aware(v[7])
        prl.save()


def price_list_product():
    data = table_data(old_data['tb_bangGiaSanPham'])
    product_prices = list()
    for k, v in enumerate(data):
        if k <= 1:
            app_log.info(v)
        insert = {
            "price_list": v[1],
            "product": v[2],
            "price": v[5],
            "quantity_in_box": v[6],
            "point": v[7],
        }
        app_log.info(v)
        app_log.info(insert)
        pl = PriceList.objects.get(id=v[1])
        prod = Product.objects.get(id=v[2])
        app_log.info(f"{pl} - {v[2]}")
        product_price = ProductPrice(price_list=pl, product=prod, price=v[5], quantity_in_box=v[6], point=v[7])
        product_prices.append(product_price)
    ProductPrice.objects.bulk_create(product_prices)


"""
tb_toa
tb_toaDetail
"""


def insert_order():
    start_time = time.time()
    for a in range(0, 1):
        i = (5000 * a)
        y = 5000 + (5000 * a)
        try:
            app_log.info(f"Get data from: {i} - {y}")
            data = table_data_2(old_data['tb_toa'], '*', {'start': i, 'end': y})
            process_order(data)
        except Exception as e:
            app_log.error(f"\nWhen get data from: {i} - {y}\n")
            raise e
    app_log.info(f"---------------------- FINISH ------------------------")
    app_log.debug(f"Complete INSERT ORDER time: {time.time() - start_time} seconds")
    app_log.info(f"Complete INSERT ORDER time: {time.time() - start_time} seconds")


def process_order(data):
    with transaction.atomic():
        list_data_backup = list()
        list_order = list()
        list_order_update = list()
        for k, v in enumerate(data):
            if k <= 1:
                app_log.info(f"Processing order: {v[0]}")
                date_company_get = make_aware(v[2]) if v[2] is not None else None
                check_date = make_aware(v[8]).date()
                price_lists = PriceList.objects.filter(date_start__lte=check_date, date_end__gte=check_date)
                price_list = price_lists.first().id if price_lists.exists() else str(None)
                insert_backup = {
                    'order_id': v[0],
                    'date_get': v[1],
                    'date_company_get': date_company_get,
                    'client_id': v[3],
                    'date_delay': v[5],
                    'price_list_id': price_list,
                    'clientlv1_id': v[11],
                    'list_type': v[12],
                    'is_so': v[14],
                    'id_so': v[15],
                    'id_offer_consider': v[16],
                    'note': v[6],
                    'created_by': v[7],
                    'created_at': make_aware(v[8]),
                }
                list_data_backup.append(OrderBackup(**insert_backup))

                try:
                    client = User.objects.get(id=v[3])
                except User.DoesNotExist:
                    client = None
                notes = json.dumps({"notes": str(v[6])}) if client is not None else json.dumps(
                    {"notes": str(v[6]), "client_id": v[3]})
                # app_log.info(f"Check character: note - {len(str(notes))} | id_so - {len(str(v[15]))} | "
                #              f"id_offer_consider - {len(str(v[16]))}")
                date_company_get = make_aware(v[2]) if v[2] is not None else None
                insert = {
                    "date_get": v[1],
                    "date_company_get": date_company_get,
                    "client_id": client,
                    "date_delay": v[5],
                    "list_type": v[12],
                    "is_so": v[14],
                    "id_so": v[15],
                    "id_offer_consider": v[16],
                    "created_by": v[7],
                    "note": notes,
                    "status": v[9],
                }
                create_at = make_aware(v[8])
                order = Order(id=v[0], **insert)
                list_order.append(order)
                check_date = make_aware(v[8]).date()
                price_lists = PriceList.objects.filter(date_start__lte=check_date, date_end__gte=check_date).first()
                order_update = Order(id=v[0], price_list_id=price_lists, created_at=create_at)
                list_order_update.append(order_update)
            else:
                break
        app_log.info(f"Inserting backup")
        Order.objects.bulk_create(list_order, ignore_conflicts=True)
        Order.objects.bulk_update(list_order_update, ['price_list_id', 'created_at'])
        OrderBackup.objects.bulk_create(list_data_backup, ignore_conflicts=True)


def insert_order_detail():
    start_time = time.time()
    max_num = count_table_items(old_data['tb_toaDetail'])
    for a in range(0, 50):
        i = (5000 * a)
        y = 5000 + (5000 * a)
        if y > max_num:
            y = max_num
        try:
            app_log.info(f"--\nGet data from: {i} - {y} \n--\n")
            data = table_data(old_data['tb_toaDetail'], '*', {'start': i, 'end': y})
            process_order_detail(data)
        except Exception as e:
            app_log.error(f"\nWhen get data from: {i} - {y}\n")
            raise e
        if y == max_num:
            break
    app_log.debug(f"---------------------- FINISH ------------------------")
    app_log.debug(f"Complete INSERT ORDER DETAILS time: {time.time() - start_time} seconds")
    app_log.info(f"Complete INSERT ORDER DETAILS time: {time.time() - start_time} seconds")


def process_order_detail(data):
    order_details_list = list()
    order_backup_details = list()
    for k, v in enumerate(data):
        if k == 1:
            app_log.info("---")
            app_log.info(v)

        note = {}
        try:
            order = Order.objects.get(id=v[1])
        except Order.DoesNotExist:
            order = None
            note['order_id'] = f"{v[1]} not found"

        try:
            product = Product.objects.get(id=v[2])
        except Product.DoesNotExist:
            product = None
            note['product_id'] = f"{v[2]} not found"

        insert = {
            "order_quantity": v[3],
            "order_box": v[4],
            "price_list_so": v[8],
            "note": note
        }
        app_log.info(f"Inserting: {order} - {product}")
        backup = OrderBackupDetail(id=v[0], order_id=v[1], product_id=v[2], order_quantity=v[3], order_box=v[4],
                                   product_price=v[5], quantity_in_box=v[6], point_get=v[7], price_list_so=v[8])
        order_backup_details.append(backup)

        try:
            if order.price_list_id is not None:
                price = ProductPrice.objects.filter(product=product, price_list=order.price_list_id).first()
                if price is not None:
                    order_detail_price = v[3] * price.price
                else:
                    order_detail_price = v[3] * v[5]
                point = v[7] * v[4] if v[7] is not None else 0
                insert['product_price'] = order_detail_price
                insert['point_get'] = point
                order_detail = OrderDetail(id=v[0], product_id=product, order_id=order, **insert)
                order_details_list.append(order_detail)
        except AttributeError:
            pass

    OrderDetail.objects.bulk_create(order_details_list, ignore_conflicts=True)
    OrderBackupDetail.objects.bulk_create(order_backup_details, ignore_conflicts=True)


def insert_special_offer():
    special_offers = list()
    special_offers_update = list()
    special_offer_product = list()

    data = table_data(old_data['tb_UuDai'])
    for k, v in enumerate(data):
        if k == 1:
            app_log.info(f"Test data: {v}")
        insert_data = {
            'id': v[11],
            'order_id': v[10],
            'created_at': make_aware(v[7]),
            'notes': v[6],
            'quantity_offer': float(v[4]),
            'value_sale_off': int(v[3]),
            'product_id': v[2],
            'client_id': v[1],
            'date_get': v[0]
        }
        so = SpecialOffer(id=v[11], name=f'Uu đai {v[11]}', box_can_use=int(v[4]), created_by=v[8])
        special_offers.append(so)

        try:
            check_date = make_aware(v[0]).date()
        except AttributeError:
            check_date = make_aware(v[7]).date()

        product = Product.objects.filter(id=v[2]).first()
        price_lists = PriceList.objects.filter(date_start__lte=check_date, date_end__gte=check_date).first()

        price = 0
        quantity_in_box = 0
        point = 0
        notes_dict = {"notes": v[6], "reference_order": v[11], "product_id": str(v[11]), "client_id": v[1]}
        if price_lists is not None and product is not None:
            product_price = ProductPrice.objects.filter(price_list=price_lists, product=product).first()
            if product_price is not None:
                price = product_price.price
                quantity_in_box = product_price.quantity_in_box
                point = product_price.point
            else:
                notes_dict['price_list'] = f"{price_lists}"
                notes_dict['product_price'] = f"Not found ProductPrice(price_list={price_lists}, product={product})"

        so_product = SpecialOfferProduct(special_offer=so, product=product,
                                         cashback=int(v[3]),
                                         price=price,
                                         point=point,
                                         quantity_in_box=quantity_in_box
                                         )
        note = json.dumps(notes_dict)
        so_update = SpecialOffer(id=v[11], created_at=make_aware(v[7]), note=note)
        special_offers_update.append(so_update)

        special_offer_product.append(so_product)
        app_log.info(f"Test data: {insert_data}")
    SpecialOffer.objects.bulk_create(special_offers)
    SpecialOffer.objects.bulk_update(special_offers_update, ['created_at', 'note'])
    SpecialOfferProduct.objects.bulk_create(special_offer_product)


def insert_detail_order():
    start_time = time.time()
    max_num = count_table_items(old_data['tb_toaDetail'])
    end_num = max_num / 5000
    for a in range(math.ceil(end_num) - 1, math.ceil(end_num)):
        i = (5000 * a)
        y = 5000 + (5000 * a)
        if y > max_num:
            y = max_num
        try:
            app_log.info(f"--\nGet data from: {i} - {y} \n--\n")
            data = table_data(old_data['tb_toaDetail'], '*', {'start': i, 'end': y})
            process_order_detail(data)
        except Exception as e:
            app_log.error(f"\nWhen get data from: {i} - {y}\n")
            raise e
        if y == max_num:
            break
    app_log.debug(f"---------------------- FINISH ------------------------")
    app_log.debug(f"Complete INSERT ORDER DETAILS time: {time.time() - start_time} seconds")
    app_log.info(f"Complete INSERT ORDER DETAILS time: {time.time() - start_time} seconds")


def update_order_details():
    start_time = time.time()
    app_log.info(f"Start update details")

    orders_with_details = Order.objects.annotate(
        has_details=Exists(OrderDetail.objects.filter(order_id=OuterRef('id')))
    ).filter(has_details=True, order_price__isnull=False).exclude(order_price__gt=0).order_by('-id')

    total_count = orders_with_details.count()

    chunk_size = 3000

    time_loop = math.ceil(total_count / chunk_size)
    for a in range(time_loop):
        start_time_2 = time.time()

        start_item = a * chunk_size
        end_item = start_item + chunk_size
        if end_item > total_count:
            end_item = total_count

        try:
            app_log.info(f"--\nGet data from: {start_item} - {end_item} \n--\n")
            paginator = Paginator(orders_with_details, chunk_size)
            page = paginator.page(a + 1)

            process_small_order_chunk(page.object_list)
        except Exception as e:
            app_log.error(f"\nWhen get data from: {start_item} - {end_item}\n")
            raise e

        app_log.info(f"Complete UPDATE ORDER items {start_item} - {end_item}: {time.time() - start_time_2} seconds")
        if end_item == total_count:
            break

    app_log.info(f"Complete UPDATE ORDER time: {time.time() - start_time} seconds")


def process_small_order_chunk(orders):
    with transaction.atomic():
        list_orders_update = []

        for i, order in enumerate(orders):
            order_details = order.order_detail.all()
            total_price = 0
            for detail in order_details:
                product_price = detail.product_price or 0
                total_price += product_price
            order.order_price = total_price
            list_orders_update.append(order)
            app_log.info(f"{order.id} - {total_price}")
        Order.objects.bulk_update(list_orders_update, ['order_price'])


def update_nvtt():
    start_time = time.time()
    app_log.info(f"Start update details")

    orders = Order.objects.filter(client_id__isnull=False).exclude(nvtt_id__isnull=False).order_by('-id')

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

            process_update_nvtt(page.object_list)
        except Exception as e:
            app_log.error(f"\nWhen get data from: {start_item} - {end_item}\n")
            raise e

        app_log.info(f"Complete UPDATE ORDER items {start_item} - {end_item}: {time.time() - start_time_2} seconds")
        if a == 1:
            break
        if end_item == total_count:
            break

    app_log.info(f"Complete UPDATE ORDER time: {time.time() - start_time} seconds")


def process_update_nvtt(orders):
    with transaction.atomic():
        list_orders_update = []
        for i, order in enumerate(orders):
            order.nvtt_id = order.client_id.clientprofile.nvtt_id
            app_log.info(f"Test: {order.id} - {order.nvtt_id}")

            list_orders_update.append(order)
        Order.objects.bulk_update(list_orders_update, ['nvtt_id'])


def update_order():
    update_order_details()
    update_nvtt()


def insert_old_data():
    # price_list()
    # price_list_product()
    # insert_special_offer()
    insert_order()
    insert_order_detail()


# from utils.insert_db.get_old_data import


if __name__ == '__main__':
    insert_old_data()

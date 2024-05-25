import time

from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.utils.timezone import make_aware

from account.models import User
from app.logs import app_log
from marketing.company.models import Company
from marketing.order.models import Order, OrderDetail
from marketing.price_list.models import PriceList, ProductPrice
from marketing.product.models import Product, UseObject, UseFor, ProductCategory, CategoryDetail, RegistrationCert, \
    Producer, RegistrationUnit, ProductType
from user_system.client_group.models import ClientGroup
from user_system.client_profile.models import ClientProfile
from user_system.employee_profile.models import EmployeeProfile, Position
from utils.helpers import table_data, normalize_vietnamese, table_data_2
from utils.constants import (old_data, maNhomND as farmerID, tenNhomND as farmerGroupName)


def append_kh():
    type_kh = "client"
    ctx = {'users': [], 'profiles': []}
    data = table_data(old_data['tb_kh'])
    for k, v in enumerate(data):
        if k == 1:
            print(v)
        client_group_id = ClientGroup.objects.filter(id=v[3]).first()
        code_client_lv1 = v[11] if v[11] != '' else None
        data_profile = {"register_name": v[1], "organization": v[2], "client_group_id": client_group_id,
                        "nvtt_id": v[4], "address": v[7], "client_lv1_id": code_client_lv1, "created_by": v[8]}
        created_time = make_aware(v[8])
        phone = v[5] if v[5] != '' else None
        pw = v[0].lower() if v[10] == '' or v[10] is None else v[10]
        hash_pw = make_password(pw)
        obj, created = User.objects.get_or_create(id=v[0], defaults={"user_type": type_kh,
                                                                     "password": hash_pw})
        obj.created_at = created_time
        obj.save()
        try:
            if phone is not None and len(phone) <= 24:
                obj.phone_numbers.get_or_create(phone_number=phone)
        except IntegrityError:
            pass

        if created:
            print(f"User {v[0]} was created successfully.")
        else:
            print(f"User {v[0]} was existed, skipping...")
        obj, created = ClientProfile.objects.get_or_create(client_id=obj, defaults=data_profile)
        if created:
            print(f"User profile {v[0]} was created successfully.")
            obj.created_at = created_time
            obj.save()
        else:
            print(f"User profile {v[0]} was existed, skipping...")
    return ctx


def append_nv():
    type_nv = "employee"
    ctx = {'users': [], 'profiles': []}
    data = table_data(old_data['tb_nhanvien'])
    for k, v in enumerate(data):
        created_time = make_aware(v[65])
        print(created_time)
        if k == 1:
            print(v)
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
            print(f"User {v[0]} was created successfully.")
        else:
            print(f"User {v[0]} was existed, skipping...")

        obj, created = EmployeeProfile.objects.get_or_create(employee_id=obj,
                                                             defaults={'fullname': f"{v[2]} {v[3]}", 'gender': v[5]})
        obj.created_at = created_time
        obj.save()
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
        obj.created_at = make_aware(v[4])
        if created:
            print(f"Created new Group id: {v[2]}")
        else:
            print(f"Group id {v[2]} already existed, passing...")
    obj, created = ClientGroup.objects.get_or_create(id=farmerID, defaults={'name': farmerGroupName})
    if created:
        print(f"Created new Group id: {farmerID}")
    else:
        print(f"Group id {farmerID} already existed, passing...")


# Get old company
def add_old_company(apps, schema_editor):
    data = table_data(old_data['tb_congty'])
    for k, v in enumerate(data):
        try:
            company = Company.objects.create(id=v[0], name=v[1], note=v[2], color_code=v[5])
            print(f"Added company {v[1]} - {v[0]}")
            company.created_at = make_aware(v[3])
            company.save()
        except Exception as e:
            print(f"----- ERROR -----")
            print(f"Message: Error when adding company.")
            print(e)
            raise Exception(e)


# Adding old Product
def old_product_type():
    data = table_data(old_data['tb_loaiThuoc'])
    print(f"--------------- ADDING PRODUCT TYPE --------------")
    for i, k in enumerate(data):
        print(f"Adding product type: {k[1]}")
        _type, _ = ProductType.objects.get_or_create(id=k[0], name=k[1])


def old_product_category():
    data = table_data(old_data['tb_thuoc'])
    print(f"---------- ADDING PRODUCT CATEGORY ----------")
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
        print(f"Adding product category: {v[0]} - {v[1]}")
        product_cate, _ = ProductCategory.objects.get_or_create(id=v[0], defaults=insert_data)
        product_cate.created_at = make_aware(v[3])
        product_cate.save()


def old_product():
    data = table_data(old_data['tb_sanpham'])
    print(f"---------- ADDING PRODUCT ----------")
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
                    insert['note'] = "Not valid Category, borrow another category."
            print(f"Adding product: {v[0]} - {v[1]}")
            product, _ = Product.objects.get_or_create(id=v[0], defaults=insert)
            product.created_at = make_aware(v[5])
            product.save()
    except Exception as e:
        print(f"----- ERROR -----")
        print(f"Message: Error when adding data to product.")
        print(e)
        raise e


def old_cate_detail():
    data = table_data(old_data['tb_thuocChitiet'])
    norm_vn = normalize_vietnamese
    print(f"--------------- ADDING CATEGORY DETAIL --------------")
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
        print(f"Adding category detail: {v[1]}")
        # print(insert)
        cate_data = CategoryDetail.objects.get_or_create(**insert)


def check_filter(data, i=0):
    i += 1
    note = False
    if i == 0:
        category = ProductCategory.objects.filter(id=data)
    else:
        category = ProductCategory.objects.filter(id__icontains=data)
        note = True
    print(f"Data: {data}")
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
            print(v)
            insert = {
                "id": v[0],
                "name": v[1],
                "date_start": v[2],
                "date_end": v[3],
                "created_by": v[8],
                "created_at": v[7]
            }
            print(insert)
        prl = PriceList.objects.create(id=v[0], name=v[1], date_start=v[2],
                                       date_end=v[3], created_by=v[8])
        prl.created_at = make_aware(v[7])
        prl.save()


def price_list_product():
    data = table_data(old_data['tb_bangGiaSanPham'])
    for k, v in enumerate(data):
        if k <= 3:
            print(v)
        insert = {
            "price_list": v[1],
            "product": v[2],
            "price": v[5],
            "quantity_in_box": v[6],
            "point": v[7],
        }
        print(v)
        print(insert)
        pl = PriceList.objects.get(id=v[1])
        prod = Product.objects.get(id=v[2])
        print(f"{pl} - {v[2]}")
        ProductPrice.objects.create(price_list=pl, product=prod, price=v[5], quantity_in_box=v[6], point=v[7])


"""
tb_toa
tb_toaDetail
"""


def insert_order():
    start_time = time.time()
    for a in range(5, 40):
        i = 1 + (5000 * a)
        y = 5000 + (5000 * a)
        data = table_data_2(old_data['tb_toa'], '*', {'start': i, 'end': y})
        process_order(data)
        print(f"Get data from: {i} - {y}")
    print(f"---------------------- FINISH ------------------------")
    app_log.debug(f"Complete INSERT ORDER time: {time.time() - start_time} seconds")
    print(f"Complete INSERT ORDER time: {time.time() - start_time} seconds")


def process_order(data):
    for k, v in enumerate(data):
        if k == 1:
            print(v)
        print(f"Client_id: {v[3]}")
        try:
            client = User.objects.get(id=v[3])
        except User.DoesNotExist:
            client = None
        notes = v[6] if client is not None else v[6] + f" | User not found: {v[3]}"
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
        order, _ = Order.objects.get_or_create(id=v[0], defaults=insert)
        print(f"Inserting order: {order}")
        order.created_at = create_at
        order.save()
        check_date = make_aware(v[8]).date()
        price_lists = PriceList.objects.filter(date_start__lte=check_date, date_end__gte=check_date)
        if price_lists.exists():
            order.price_list_id = price_lists.first()
            order.save()
            print(price_lists.first())


def insert_order_detail():
    start_time = time.time()
    for a in range(0, 50):
        i = 1 + (5000 * a)
        y = 5000 + (5000 * a)
        print(f"--\nGet data from: {i} - {y} \n--\n")
        data = table_data(old_data['tb_toaDetail'], '*', {'start': i, 'end': y})
        process_order_detail(data)
    app_log.debug(f"---------------------- FINISH ------------------------")
    app_log.debug(f"Complete INSERT ORDER DETAILS time: {time.time() - start_time} seconds")
    print(f"Complete INSERT ORDER DETAILS time: {time.time() - start_time} seconds")


def process_order_detail(data):
    for k, v in enumerate(data):
        if k == 1:
            print("---")
            print(v)
        note = ""
        try:
            order = Order.objects.get(id=v[1])
        except Order.DoesNotExist:
            order = None
            note += f"order_id: {v[1]} not found"
        try:
            product = Product.objects.get(id=v[2])
        except Product.DoesNotExist:
            product = None
            note = "" if note == "" else note + ", "
            note += f"product_id: {v[2]} not found"

        insert = {
            "order_quantity": v[3],
            "order_box": v[4],
            "point_get": v[7],
            "price_list_so": v[8],
            "note": note
        }
        print("")
        app_log.debug(f"Inserting: {order} - {product}")
        order_detail, _ = OrderDetail.objects.get_or_create(product_id=product, order_id=order, defaults=insert)
        try:
            if order.price_list_id is not None:
                price = ProductPrice.objects.filter(product=product, price_list=order.price_list_id).first()
                order_detail.product_price = order_detail.order_quantity * price.price
                order_detail.save()
        except AttributeError:
            pass
        print(order_detail)


def insert_old_data():
    # price_list()
    # price_list_product()
    insert_order()
    insert_order_detail()


if __name__ == '__main__':
    insert_old_data()

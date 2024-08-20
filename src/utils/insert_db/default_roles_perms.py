from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from pyodbc import IntegrityError

from account.models import User, Perm, GroupPerm
from app.logs import app_log
from marketing.order.models import Order, OrderDetail
from marketing.price_list.models import SpecialOffer, SpecialOfferProduct, PriceList, ProductPrice
from marketing.product.models import Product, ProductCategory, ProductType, RegistrationUnit, Producer, \
    RegistrationCert, UseObject, UseFor, CategoryDetail
from utils.constants import perm_actions


def create_initial_permission():
    content_types = ContentType.objects.all()

    for i, content_type in enumerate(content_types):
        app_log.info("\n_________ || --- || __________")
        app_log.info(f"Perm: {i} - {content_type.model}")
        if i > 6:
            perm_name = f'{content_type.app_label}_{content_type.model}'
            tasks = perm_actions['fall']
            for task in tasks:
                perm_name_ = f'{task}_{perm_name}'
                try:
                    perm, created = Perm.objects.get_or_create(
                        name=perm_name_,
                        defaults={'note': f'{task.capitalize()} {content_type.model}', 'content_type': content_type}
                    )
                    if created:
                        app_log.info(f"Created new permission: {perm_name}")
                    else:
                        app_log.info(f"Permission {perm_name} already exists.")
                except IntegrityError:
                    app_log.info(f"Failed to create permission due to an integrity error: {perm_name}")
                    continue


def set_user_perm(user_instance, add):
    app_log.info(user_instance)
    content_type = ContentType.objects.get_for_model(user_instance)
    perm_name = f'{content_type.app_label}_{content_type.model}_{user_instance.id}'
    tasks = perm_actions['full']
    for task in tasks:
        perm_name_ = f'{task}_{perm_name}'
        app_log.info(f"Adding permission: {perm_name_}")
        try:
            perm_, _ = Perm.objects.get_or_create(
                name=perm_name_,
                defaults={'note': f'{task.capitalize()} {content_type.model}', 'content_type': content_type})
            if add and task != 'destroy':
                user_instance.perm_user.add(perm_, through_defaults={'allow': True})
        except IntegrityError:
            continue


def set_farmer_role():
    farmer_group = GroupPerm.objects.get(name='farmer')
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail,
                  ProductCategory]
    add_group_perm(farmer_group, [perm_actions['view']], view_group)


# Role Khách hàng/ Đại lý
def set_client_role():
    client_group, _ = GroupPerm.objects.get_or_create(name='client', defaults={'allow': True})
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail,
                  ProductCategory, Product, ProductPrice]
    add_group_perm(client_group, [perm_actions['view']], view_group)

    create_group = [Order, OrderDetail]
    add_group_perm(client_group, [perm_actions['create']], create_group)


def set_employee_role():
    employee_group, _ = GroupPerm.objects.get_or_create(name='employee',
                                                        defaults={'allow': True, 'display_name': 'Nhân viên Cty',
                                                                  'level': 7})
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail,
                  ProductCategory, Product, ProductPrice]
    add_group_perm(employee_group, [perm_actions['view']], view_group)

    create_group = [Order, OrderDetail]
    add_group_perm(employee_group, [perm_actions['create']], create_group)


def set_NVTT_role():
    set_employee_role()
    employee_group = GroupPerm.objects.get(name='employee')
    nvt_group, _ = GroupPerm.objects.get_or_create(name='nvtt',
                                                   defaults={'allow': True, 'display_name': 'Nhân viên Thị Trường',
                                                             'level': 7, 'parent_group': employee_group})
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail,
                  ProductCategory, Product, ProductPrice]
    add_group_perm(nvt_group, [perm_actions['view']], view_group)

    view_special_group = [Product, PriceList, ProductPrice, SpecialOffer, SpecialOfferProduct]
    add_group_perm(nvt_group, [perm_actions['view']], view_special_group)


def set_NPP_role():
    npp_group, _ = GroupPerm.objects.get_or_create(name='npp', defaults={'allow': True})
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail,
                  ProductCategory, Product, ProductPrice]
    add_group_perm(npp_group, [perm_actions['view']], view_group)

    create_group = [Order, OrderDetail]
    add_group_perm(npp_group, [perm_actions['create']], create_group)


def set_client_default():
    farmer_group, _ = GroupPerm.objects.get_or_create(name='farmer',
                                                      defaults={'allow': True, 'display_name': 'Nông dân', 'level': 2})
    client_group, _ = GroupPerm.objects.get_or_create(name='client',
                                                      defaults={'allow': True, 'display_name': 'Khách hàng',
                                                                'level': 4})

    client_lv1, _ = GroupPerm.objects.get_or_create(name='client_lv1',
                                                    defaults={'allow': True, 'display_name': 'Khách hàng cấp 1',
                                                              'level': 5, 'parent_group': client_group})
    client_lv2, _ = GroupPerm.objects.get_or_create(name='client_lv2',
                                                    defaults={'allow': True, 'display_name': 'Khách hàng cấp 2',
                                                              'level': 5, 'parent_group': client_group})
    client_vip, _ = GroupPerm.objects.get_or_create(name='client_vip',
                                                    defaults={'allow': True, 'display_name': 'Khách hàng VIP',
                                                              'level': 5, 'parent_group': client_group})
    client_lv1_north, _ = GroupPerm.objects.get_or_create(name='client_lv1_north',
                                                          defaults={'allow': True,
                                                                    'display_name': 'Khách hàng cấp 1 Miền Bắc',
                                                                    'level': 5,
                                                                    'parent_group': client_lv1})
    test_group, _ = GroupPerm.objects.get_or_create(name='test', defaults={'allow': True, 'display_name': 'Nhóm test'})
    npp, _ = GroupPerm.objects.get_or_create(name='npp', defaults={'allow': True, 'display_name': 'Nhà phân phối',
                                                                   'parent_group': client_group, 'level': 6})


def auto_role():
    set_client_default()
    set_farmer_role()
    set_client_role()
    set_NVTT_role()
    set_NPP_role()


def add_group_perm(group, actions: list, models):
    with transaction.atomic():
        for model in models:
            model_content = ContentType.objects.get_for_model(model)
            for action in actions:
                app_log.info(f"Test models: {model_content}")
                app_log.info(f"Test {action}")
                perm_name = f'{action}_{model_content.app_label}_{model_content.model}'
                app_log.info(f"Permission: {perm_name}")
                perm = Perm.objects.get(name=perm_name)
                group.perm.add(perm, through_defaults={'allow': True})

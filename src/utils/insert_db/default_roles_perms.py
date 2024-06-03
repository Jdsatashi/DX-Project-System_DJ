from django.contrib.contenttypes.models import ContentType
from pyodbc import IntegrityError

from account.models import User, Perm, GroupPerm
from app.logs import app_log
from marketing.order.models import Order, OrderDetail
from marketing.price_list.models import SpecialOffer, SpecialOfferProduct, PriceList, ProductPrice
from marketing.product.models import Product, ProductCategory, ProductType, RegistrationUnit, Producer, \
    RegistrationCert, UseObject, UseFor, CategoryDetail
from utils.constants import acquy


def create_initial_permission():
    content_types = ContentType.objects.all()

    for i, content_type in enumerate(content_types):
        app_log.info("\n_________ || --- || __________")
        app_log.info(f"Perm: {i} - {content_type.model}")
        if i > 6:
            perm_name = f'{content_type.app_label}_{content_type.model}'
            tasks = acquy['full']
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
    user_ins = User.objects.get(username=user_instance)
    content_type = ContentType.objects.get_for_model(user_ins)
    perm_name = f'{content_type.app_label}_{content_type.model}_{user_instance.id}'
    tasks = acquy['full']
    for task in tasks:
        perm_name_ = f'{task}_{perm_name}'
        app_log.info(f"Adding permission: {perm_name}")
        try:
            perm_, _ = Perm.objects.get_or_create(
                name=perm_name_,
                defaults={'note': f'{task.capitalize()} {content_type.model}', 'content_type': content_type})
            if add and task != 'destroy':
                user_ins.perm_user.add(perm_, through_defaults={'allow': True})
        except IntegrityError:
            continue


def set_farmer_role():
    farmer_group, _ = GroupPerm.objects.get_or_create(name='farmer', defaults={'allow': True})
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail,
                  ProductCategory]
    add_group_perm(farmer_group, acquy['view'], view_group)


# Role Khách hàng/ Đại lý
def set_client_role():
    client_group, _ = GroupPerm.objects.get_or_create(name='client', defaults={'allow': True})
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail,
                  ProductCategory]
    add_group_perm(client_group, acquy['view'], view_group)

    create_group = [Order, OrderDetail]
    add_group_perm(client_group, [acquy['create']], create_group)


def set_NVTT_role():
    nvt_group, _ = GroupPerm.objects.get_or_create(name='nvtt', defaults={'allow': True})
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail,
                  ProductCategory]
    add_group_perm(nvt_group, acquy['view'], view_group)

    view_special_group = [Product, PriceList, ProductPrice, SpecialOffer, SpecialOfferProduct]
    add_group_perm(nvt_group, acquy['view'], view_special_group)


def set_NPP_role():
    npp_group, _ = GroupPerm.objects.get_or_create(name='npp', defaults={'allow': True})
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail,
                  ProductCategory]
    add_group_perm(npp_group, acquy['view'], view_group)

    view_special_group = [Product, PriceList, ProductPrice, SpecialOffer, SpecialOfferProduct]
    add_group_perm(npp_group, acquy['view'], view_special_group)


def set_client_default():
    farmer_group, _ = GroupPerm.objects.get_or_create(name='farmer',
                                                      defaults={'allow': True, 'description': 'Nông dân'})
    client_group, _ = GroupPerm.objects.get_or_create(name='client',
                                                      defaults={'allow': True, 'description': 'Khách hàng'})

    client_lv1, _ = GroupPerm.objects.get_or_create(name='client_lv1',
                                                    defaults={'allow': True, 'description': 'Khách hàng cấp 1',
                                                              'parent_group': client_group})
    client_lv2, _ = GroupPerm.objects.get_or_create(name='client_lv2',
                                                    defaults={'allow': True, 'description': 'Khách hàng cấp 2',
                                                              'parent_group': client_group})
    client_vip, _ = GroupPerm.objects.get_or_create(name='client_vip',
                                                    defaults={'allow': True, 'description': 'Khách hàng VIP',
                                                              'parent_group': client_group})
    client_lv1_north, _ = GroupPerm.objects.get_or_create(name='client_lv1_north', defaults={'allow': True,
                                                                                             'description': 'Khách hàng cấp 1 Miền Bắc',
                                                                                             'parent_group': client_lv1})
    test_group, _ = GroupPerm.objects.get_or_create(name='test', defaults={'allow': True, 'description': 'Nhóm test'})


def auto_role():
    set_client_default()
    set_farmer_role()
    set_client_role()
    set_NVTT_role()
    set_NPP_role()


def add_group_perm(group, actions: list, models):
    for model in models:
        model_content = ContentType.objects.get_for_model(model)
        for action in actions:
            app_log.info(f"Test models: {model_content}")
            app_log.info(f"Test {action}")
            perm_name = f'{action}_{model_content.app_label}_{model_content.model}'
            app_log.info(f"Permission: {perm_name}")
            perm = Perm.objects.get(name=perm_name)
            group.perm.add(perm, through_defaults={'allow': True})

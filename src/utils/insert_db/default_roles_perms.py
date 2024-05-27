from django.contrib.contenttypes.models import ContentType

from account.models import User, Perm, GroupPerm
from marketing.order.models import Order
from marketing.product.models import Product, ProductCategory, ProductType, RegistrationUnit, Producer, \
    RegistrationCert, UseObject, UseFor, CategoryDetail
from utils.constants import acquy


def set_user_perm(user_instance):
    user_ins = User.objects.get(username=user_instance)
    content_type = ContentType.objects.get_for_model(user_ins)
    perm_name = f'{content_type.app_label}_{content_type.model}_{user_instance.id}'
    tasks = acquy['full']
    for task in tasks:
        perm_name_ = f'{task}_{perm_name}'
        print(f"Adding permission: {perm_name}")
        Perm.objects.create(name=perm_name_, note=f'{task.capitalize()} {content_type.model}',
                            content_type=content_type)


def set_farmer_role():
    farmer_group, _ = GroupPerm.objects.get_or_create(name='farmer', defaults={'allow': True})
    order_content = ContentType.objects.get_for_model(Order)
    view_group = [ProductType, RegistrationUnit, Producer, RegistrationCert, UseObject, UseFor, CategoryDetail]
    for model in view_group:
        model_content = ContentType.objects.get_for_model(model)
        action_view = acquy['view']
        for action in action_view:
            perm_name = f'{action}_{model_content.app_label}_{model_content.model}'
            perm = Perm.objects.get(name=perm_name)
            farmer_group.permissions.add(perm)
    perm_name = f'create_{order_content.app_label}_{order_content.model}'
    order_perm = Perm.objects.get(name=perm_name)
    farmer_group.permissions.add(order_perm)

from django.contrib.contenttypes.models import ContentType
from pyodbc import IntegrityError

from account.models import User, Perm, GroupPerm
from marketing.order.models import Order
from marketing.product.models import Product, ProductCategory, ProductType, RegistrationUnit, Producer, \
    RegistrationCert, UseObject, UseFor, CategoryDetail
from utils.constants import acquy


def create_initial_permission():
    content_types = ContentType.objects.all()

    for i, content_type in enumerate(content_types):
        print("\n_________ || --- || __________")
        print(f"Perm: {i} - {content_type.model}")
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
                        print(f"Created new permission: {perm_name}")
                    else:
                        print(f"Permission {perm_name} already exists.")
                except IntegrityError:
                    print(f"Failed to create permission due to an integrity error: {perm_name}")
                    continue


def set_user_perm(user_instance, add):
    print(user_instance)
    user_ins = User.objects.get(username=user_instance)
    content_type = ContentType.objects.get_for_model(user_ins)
    perm_name = f'{content_type.app_label}_{content_type.model}_{user_instance.id}'
    tasks = acquy['full']
    for task in tasks:
        perm_name_ = f'{task}_{perm_name}'
        print(f"Adding permission: {perm_name}")
        try:
            perm_, _ = Perm.objects.get_or_create(
                name=perm_name_,
                defaults={'note': f'{task.capitalize()} {content_type.model}', 'content_type': content_type})
            if add:
                user_ins.perm_user.add(perm_, through_defaults={'allow': True})
        except IntegrityError:
            continue


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

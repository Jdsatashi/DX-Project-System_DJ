from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from pyodbc import IntegrityError

from account.models import User, Perm
from marketing.order.models import Order
from utils.constants import perm_actions, admin_role
from utils.insert_db.default_roles_perms import set_user_perm


def user_perm():
    users = User.objects.all().exclude(group_user__name=admin_role)
    for user in users:
        # set_user_perm(user, True)

        content_type = ContentType.objects.get_for_model(user)
        perm_name = f'{content_type.app_label}_{content_type.model}_{user.id}'
        tasks = perm_actions['full']
        all_perm = Perm.objects.filter(name=f'all_{perm_name}').first()
        # all_perm = user.perm_user.filter(name=f'all_{perm_name}').first()
        if all_perm:
            print(f"_REMOVE {all_perm}")
            user.perm_user.remove(all_perm)
            all_perm.delete()
        for task in tasks:
            perm_name_ = f'{task}_{perm_name}'
            print(f"__Adding permission: {perm_name_}")
            try:
                perm_, _ = Perm.objects.get_or_create(
                    name=perm_name_,
                    defaults={'note': f'{task.capitalize()} {content_type.model}',
                              'content_type': content_type, 'object_id': user.id})
                if task != 'destroy':
                    user.perm_user.add(perm_, through_defaults={'allow': True})
            except IntegrityError:
                continue


def add_permissions_for_nvtt_users():
    nvtt_users = User.objects.filter(group_user__name='nvtt')
    for nvtt_user in nvtt_users:
        managed_users = User.objects.filter(clientprofile__nvtt_id=nvtt_user.id)
        add_permissions(nvtt_user, managed_users)


def add_permissions_for_npp_users():
    npp_users = User.objects.filter(Q(clientprofile__is_npp=True) | Q(group_user__name='npp'))
    for npp_user in npp_users:
        managed_users = User.objects.filter(clientprofile__client_lv1_id=npp_user.id)
        add_permissions(npp_user, managed_users)


def add_permissions(user_instance, managed_users):
    content_type = ContentType.objects.get_for_model(User)
    perm_name_list = f'view_{content_type.app_label}_{content_type.model}'

    for managed_user in managed_users:
        perm_name_list_ = f"{perm_name_list}_{managed_user.id}"
        print(f"Handle user: {managed_user}")

        perm_list = Perm.objects.get(
            name=perm_name_list_,
        )

        user_instance.perm_user.add(perm_list)


def update_nvtt():
    orders = Order.objects.filter(nvtt_id__isnull=True)

    total_items = orders.count()
    quantity_loop = 2000
    time_loop = total_items // quantity_loop
    for i in range(time_loop):
        start_items = i * quantity_loop
        end_items = start_items + quantity_loop
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

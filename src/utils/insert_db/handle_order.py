import re

from django.db.models import Q

from account.models import PhoneNumber
from app.logs import app_log
from marketing.order.models import Order
from marketing.price_list.models import SpecialOffer, SpecialOfferProduct


def handle_so():
    orders_so = Order.objects.filter(Q(is_so=True, id_offer_consider__isnull=False)).order_by('-id')
    ten_items = list(orders_so)[:10]
    for item in ten_items:
        print("")
        list_so_order = item.id_offer_consider.strip('_').split('_')
        app_log.info(f"Test item: {item.id}_{len(list_so_order)}")
        list_so_obj = SpecialOffer.objects.filter(id__in=list_so_order)
        app_log.info(f"List SO {list_so_obj.count()}: {list_so_obj}")


def count_cashback(order_id):
    order = Order.objects.filter(id=order_id).first()
    if order.is_so:
        list_so_order = order.id_offer_consider.strip('_').split('_')
        so_objects = SpecialOffer.objects.filter(id__in=list_so_order)
        order_details = order.order_detail.filter()

        result = dict()

        for od in order_details:
            product_id = od.product_id
            special_product = SpecialOfferProduct.objects.filter(product_id=product_id, special_offer__in=so_objects).first()
            app_log.info(f"Box {od.order_box} has cashback {special_product.cashback}")
            product_cashback = od.order_box * special_product.cashback
            result[product_id.id] = int(product_cashback)

        return result
    return None


def count_cashback_2(od_object):
    pass


def handle_phone():
    phones1 = PhoneNumber.objects.filter(Q(phone_number__regex=r'\s') | Q(phone_number__regex=r'\.') | Q(phone_number__regex=r'-'))
    phones2 = PhoneNumber.objects.filter(Q(phone_number__icontains='E8') | Q(phone_number__icontains='E9'))

    for phone in phones1:
        print(f"Handle phone: {phone.phone_number}")
        replace_phone = re.sub(r'\s|\.', '', phone.phone_number)
        print(f"Test replace phone: {replace_phone}")
        if PhoneNumber.objects.filter(phone_number=replace_phone).exists():
            phone.delete()
        else:
            phone.phone_number = replace_phone
            print(f"Handle phone 2: {phone.phone_number}")
            phone.save()

    for phone in phones2:
        replace_phone = phone.phone_number.replace('E8', '').replace('E9', '')
        if PhoneNumber.objects.filter(phone_number=replace_phone).exists():
            phone.delete()
        else:
            phone.phone_number = replace_phone
            print(f"Handle phone 2: {phone.phone_number}")
            phone.save()

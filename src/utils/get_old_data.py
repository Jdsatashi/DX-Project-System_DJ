from django.utils.timezone import make_aware

from marketing.price_list.models import PriceList, ProductPrice
from marketing.product.models import Product
from utils.constants import old_data
from utils.helpers import table_data


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
                                       date_end=v[3], created_by=v[8], created_at=v[7])
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

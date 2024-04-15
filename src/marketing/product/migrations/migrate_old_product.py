from marketing.company.models import Company
from marketing.product.models import Product, ProductCategory, RegistrationCert, Producer, RegistrationUnit, \
    ProductType, UseObject, UseFor, CategoryDetail
from utils.constants import old_data
from utils.helpers import table_data, normalize_vietnamese
from django.db import migrations


def old_product_type():
    data = table_data(old_data['tb_loaiThuoc'])
    print(f"--------------- ADDING PRODUCT TYPE --------------")
    for i, k in enumerate(data):
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
        product_cate, _ = ProductCategory.objects.get_or_create(id=v[0], defaults=insert_data)


def old_product():
    data = table_data(old_data['tb_sanpham'])
    print(f"---------- ADDING PRODUCT ----------")
    for i, v in enumerate(data):
        insert = {
            'name': v[1],
            'price': int(v[3]),
            'quantity': int(v[4]),
            'category': v[7],
            'main_id': v[8],
            'created_by': v[6],
        }
        Product.objects.get_or_create(id=v[0], defaults=insert)


def old_cate_detail():
    data = table_data(old_data['tb_thuocChitiet'])
    norm_vn = normalize_vietnamese
    print(f"--------------- ADDING CATEGORY DETAIL --------------")
    for i, v in enumerate(data):
        use_on, _ = UseObject.objects.get_or_create(id=norm_vn(v[2]), defaults={'name': v[2]})
        use_for, _ = UseFor.objects.get_or_create(id=norm_vn(v[3]), defaults={'name': v[3]})
        category = ProductCategory.objects.get(id=v[1])
        insert = {
            'cate_id': category,
            'use_object': use_on,
            'use_for': use_for,
            'dosage': v[4],
            'usage': v[5]
        }
        cate_data = CategoryDetail.objects.create(**insert)


def add_old_product(apps, schema_editor):
    try:
        old_product_type()
        old_product_category()
        old_product()
    except Exception as e:
        print(f"----- ERROR -----")
        print(f"Message: Error when adding company.")
        print(e)
        raise Exception(e)


class Migration(migrations.Migration):
    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_old_product),
    ]

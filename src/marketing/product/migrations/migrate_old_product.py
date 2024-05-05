from django.db import migrations

from utils.get_old_data import old_product_type, old_product, old_product_category, old_cate_detail


def add_old_product(apps, schema_editor):
    try:
        old_product_type()
        old_product_category()
        old_product()
        old_cate_detail()
    except Exception as e:
        print(f"----- ERROR -----")
        print(f"Message: Error when adding product.")
        print(e)
        raise Exception(e)


class Migration(migrations.Migration):
    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_old_product),
    ]

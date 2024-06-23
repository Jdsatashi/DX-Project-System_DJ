from django.db import migrations

from app.logs import app_log
from utils.insert_db.get_old_data import old_product_type, old_product, old_product_category, old_cate_detail


def add_old_product(apps, schema_editor):
    try:
        old_product_type()
        old_product_category()
        old_product()
        old_cate_detail()
    except Exception as e:
        app_log.info(f"----- ERROR -----")
        app_log.info(f"Message: Error when adding product.")
        app_log.info(e)
        raise Exception(e)


class Migration(migrations.Migration):
    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_old_product),
    ]

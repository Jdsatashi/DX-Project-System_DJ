from django.db import migrations


def old_price_list():
    pass


def migrate_old_price_list(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [('price_list', '0001_initial')]

    operations = [
        migrations.RunPython(migrate_old_price_list),
    ]

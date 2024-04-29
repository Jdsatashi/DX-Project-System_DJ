from django.db import migrations


def migrate_old_order(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [('price_list', '0001_initial')]

    operations = [
        migrations.RunPython(migrate_old_order),
    ]

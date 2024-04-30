from django.db import migrations

from utils.get_old_data import add_old_company


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_old_company),
    ]

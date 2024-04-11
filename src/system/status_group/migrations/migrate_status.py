from django.db import migrations

from system.status_group.models import Status
from utils.constants import status


def add_default_status(apps, schema_editor):
    data = status
    for v in data:
        try:
            Status.objects.create(name=v)
            print(f"Adding {v}")
        except Exception as e:
            print(f"----- ERROR -----")
            print(f"Message: Error when adding status.")
            print(e)
            raise Exception(e)


class Migration(migrations.Migration):

    dependencies = [
        ('status_group', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_default_status),
    ]

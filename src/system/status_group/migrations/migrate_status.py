from django.db import migrations

from app.logs import app_log
from system.status_group.models import Status
from utils.constants import status


def add_default_status(apps, schema_editor):
    data = status
    for v in data:
        try:
            Status.objects.create(name=v)
            app_log.info(f"Adding {v}")
        except Exception as e:
            app_log.info(f"----- ERROR -----")
            app_log.info(f"Message: Error when adding status.")
            app_log.info(e)
            raise Exception(e)


class Migration(migrations.Migration):

    dependencies = [
        ('status_group', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_default_status),
    ]

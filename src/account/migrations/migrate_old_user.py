import time

from django.db import migrations

from app.logs import app_log
from utils.insert_db.get_old_data import create_position, create_client_group_id, append_nv, append_kh


def insertDB(apps, schema_editor):
    start_time = time.time()
    create_position()
    create_client_group_id()
    append_nv()
    append_kh()
    app_log.info(f"\n__FINISHED__")
    app_log.info(f"Complete time: {time.time() - start_time} seconds")


class Migration(migrations.Migration):
    dependencies = [
        ('account', 'migrate_perm'),
    ]

    operations = [
        migrations.RunPython(insertDB),
    ]

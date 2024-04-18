import json
import os

from django.db import migrations
from account.models import User
from app.settings import PROJECT_DIR


def create_suser(apps, schema_editor):
    file_fir = os.path.join(PROJECT_DIR, 'user_adding.json')
    with open(file_fir, 'r') as file:
        superusers = json.load(file)
        for user in superusers:
            if not User.objects.filter(id=user['id']).exists():
                manager = User.objects
                manager.create_superuser(
                    id=user['id'], username=user['username'],
                    email=user['email'], phone_number=user['phone_number'],
                    password=user['password']
                )


class Migration(migrations.Migration):
    dependencies = [
        ('account', 'migrate_perm')
    ]

    operations = [
        migrations.RunPython(create_suser),
    ]

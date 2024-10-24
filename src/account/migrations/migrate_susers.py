import json
import os

from django.db import migrations
from account.models import User, Perm, GroupPerm
from app.settings import PROJECT_DIR
from django.utils import timezone


def create_suser(apps, schema_editor):
    file_fir = os.path.join(PROJECT_DIR, 'user_adding.json')
    with open(file_fir, 'r') as file:
        superusers = json.load(file)
        for user in superusers:
            if not User.objects.filter(id=user['id']).exists():
                manager = User.objects
                manager.create_superuser(
                    id=user['id'], username=user['username'], phone_number=[],
                    email=user['email'],
                    password=user['password'],
                    created_at=timezone.now()
                )


class Migration(migrations.Migration):
    dependencies = [
        ('account', 'migrate_old_user')
    ]

    operations = [
        migrations.RunPython(create_suser),
    ]

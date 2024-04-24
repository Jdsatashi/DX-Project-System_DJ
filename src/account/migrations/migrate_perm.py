from django.contrib.contenttypes.models import ContentType
from django.db import migrations

from account.models import Perm
from app.settings import MY_APPS
from utils.constants import acquy


def create_initial_permission(apps, schema_editor):
    content_types = ContentType.objects.all()

    for i, content_type in enumerate(content_types):
        print(f"Perm: {i} - {content_type.model}")
        if i > 6:
            perm_name = f'{content_type.app_label}_{content_type.model}'
            tasks = acquy['full']
            for task in tasks:
                perm_name_ = f'{task}_{perm_name}'
                print(f"Adding permission: {perm_name}")
                Perm.objects.create(name=perm_name_, note=f'{task.capitalize()} {content_type.model}')


class Migration(migrations.Migration):
    depdc = [('account', '0001_initial'), ('admin', '0001_initial')]
    for i, v in enumerate(MY_APPS):
        data = v.split('.')
        v = data[-1]
        a = (v, '0001_initial')
        depdc.append(a)
    dependencies = depdc

    operations = [
        migrations.RunPython(create_initial_permission),
    ]

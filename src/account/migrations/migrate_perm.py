from django.contrib.contenttypes.models import ContentType
from django.db import migrations

from account.models import Quyen
from utils.constants import acquy


def create_initial_permission(apps, schema_editor):
    content_types = ContentType.objects.all()

    for i, content_type in enumerate(content_types):
        if i > 6:
            quyen_name = f'{content_type.app_label}_{content_type.model}'
            tasks = acquy['full']
            for task in tasks:
                quyen_name_ = f'{task}_{quyen_name}'
                Quyen.objects.create(name=quyen_name_, mota=f'{task.capitalize()} {content_type.model}')


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_permission),
    ]

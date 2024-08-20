from django.contrib.contenttypes.models import ContentType
from django.db import migrations

from account.models import Perm, GroupPerm
from app.logs import app_log
from app.settings import MY_APPS
from utils.constants import perm_actions, admin_role


def create_initial_permission(apps, schema_editor):
    # ContentType = apps.get_model('contenttypes', 'ContentType')
    # Perm = apps.get_model('account', 'Perm')
    content_types = ContentType.objects.all()

    for i, content_type in enumerate(content_types):
        app_log.info(f"Perm: {i} - {content_type.model}")
        if i > 6:
            perm_name = f'{content_type.app_label}_{content_type.model}'
            tasks = perm_actions['fall']
            for task in tasks:
                perm_name_ = f'{task}_{perm_name}'
                app_log.info(f"Adding permission: {perm_name_}")
                Perm.objects.create(name=perm_name_, note=f'{task.capitalize()} {content_type.model}',
                                    content_type=content_type)


def create_admin_perm(apps, schema_editor):
    matching_perms = Perm.objects.filter(name__icontains='all')
    list_perms = list(matching_perms)
    group_perm, _ = GroupPerm.objects.get_or_create(name=admin_role)
    for q in list_perms:
        app_log.info(f"Add perms '{q.name}' to group {admin_role}")
        group_perm.perm.add(q.name, through_defaults={'allow': True})


class Migration(migrations.Migration):
    depdc = [('account', '0001_groupperm_level'), ('admin', '0001_initial')]
    # for i, v in enumerate(MY_APPS):
    #     data = v.split('.')
    #     v = data[-1]
    #     a = (v, '0001_initial')
    #     depdc.append(a)
    dependencies = depdc

    operations = [
        migrations.RunPython(create_initial_permission),
        migrations.RunPython(create_admin_perm),
    ]

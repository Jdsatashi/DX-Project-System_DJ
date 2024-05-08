from django.contrib.contenttypes.models import ContentType
from django.db import migrations

from account.models import Perm, GroupPerm
from app.settings import MY_APPS
from utils.constants import acquy


def create_initial_permission(apps, schema_editor):
    # ContentType = apps.get_model('contenttypes', 'ContentType')
    # Perm = apps.get_model('account', 'Perm')
    content_types = ContentType.objects.all()

    for i, content_type in enumerate(content_types):
        print(f"Perm: {i} - {content_type.model}")
        if i > 6:
            perm_name = f'{content_type.app_label}_{content_type.model}'
            tasks = acquy['full']
            for task in tasks:
                perm_name_ = f'{task}_{perm_name}'
                print(f"Adding permission: {perm_name}")
                Perm.objects.create(name=perm_name_, note=f'{task.capitalize()} {content_type.model}', content_type=content_type)


def create_draft_perm(apps, schema_editor):
    matching_perm = Perm.objects.filter(name__icontains="draft").all()
    list_drafts_perm = list(matching_perm)
    group_perm, _ = GroupPerm.objects.get_or_create(name="group_draft")
    for q in list_drafts_perm:
        group_perm.perm.add(q.name)


def create_admin_perm(apps, schema_editor):
    admin_role = "admin"
    matching_perms = Perm.objects.all()
    list_perms = list(matching_perms)
    group_perm, _ = GroupPerm.objects.get_or_create(name=admin_role)
    for q in list_perms:
        print(f"Add perms '{q.name}' to group {admin_role}")
        group_perm.perm.add(q.name)


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
        migrations.RunPython(create_draft_perm),
        migrations.RunPython(create_admin_perm),
    ]

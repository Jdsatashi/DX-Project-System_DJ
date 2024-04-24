from django.db import migrations

from account.models import Perm, GroupPerm


def create_initial_permission(apps, schema_editor):
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

    dependencies = [
        ('account', 'migrate_perm'),
    ]

    operations = [
        migrations.RunPython(create_initial_permission),
        migrations.RunPython(create_admin_perm),
    ]

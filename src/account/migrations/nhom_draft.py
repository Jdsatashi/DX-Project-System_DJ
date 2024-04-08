from django.db import migrations

from account.models import Perm, GroupPerm


def create_initial_permission(apps, schema_editor):
    matching_quyens = Perm.objects.filter(name__icontains="draft").all()
    list_drafts_quyens = list(matching_quyens)
    grorup_perm, _ = GroupPerm.objects.get_or_create(name="group_draft")
    for q in list_drafts_quyens:
        grorup_perm.quyen.add(q.name)


class Migration(migrations.Migration):

    dependencies = [
        ('account', 'migrate_old_user'),
    ]

    operations = [
        migrations.RunPython(create_initial_permission),
    ]

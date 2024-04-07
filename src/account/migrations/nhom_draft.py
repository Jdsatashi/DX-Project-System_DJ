from django.db import migrations

from account.models import Quyen, NhomQuyen


def create_initial_permission(apps, schema_editor):
    matching_quyens = Quyen.objects.filter(name__icontains="draft").all()
    list_drafts_quyens = list(matching_quyens)
    nhom_quyen, _ = NhomQuyen.objects.get_or_create(name="nhom_draft")
    for q in list_drafts_quyens:
        nhom_quyen.quyen.add(q.name)


class Migration(migrations.Migration):

    dependencies = [
        ('account', 'migrate_old_user'),
    ]

    operations = [
        migrations.RunPython(create_initial_permission),
    ]

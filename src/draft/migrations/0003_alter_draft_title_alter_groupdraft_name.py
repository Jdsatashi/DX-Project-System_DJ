# Generated by Django 5.0.1 on 2024-02-03 02:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('draft', '0002_remove_draft_group_delete_draftingroup_draft_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='draft',
            name='title',
            field=models.CharField(max_length=124, unique=True),
        ),
        migrations.AlterField(
            model_name='groupdraft',
            name='name',
            field=models.CharField(unique=True),
        ),
    ]

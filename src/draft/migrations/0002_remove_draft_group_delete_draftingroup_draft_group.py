# Generated by Django 5.0.1 on 2024-01-20 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('draft', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='draft',
            name='group',
        ),
        migrations.DeleteModel(
            name='DraftInGroup',
        ),
        migrations.AddField(
            model_name='draft',
            name='group',
            field=models.ManyToManyField(to='draft.groupdraft'),
        ),
    ]

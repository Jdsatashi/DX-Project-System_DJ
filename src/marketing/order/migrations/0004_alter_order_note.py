# Generated by Django 5.0.3 on 2024-06-23 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_orderbackupdetail_alter_orderbackup_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='note',
            field=models.TextField(null=True),
        ),
    ]

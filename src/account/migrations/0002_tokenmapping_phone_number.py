# Generated by Django 5.0.3 on 2024-07-30 19:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_grantaccess_grantaccess_unique_manager_grant_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='tokenmapping',
            name='phone_number',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='account.phonenumber'),
        ),
    ]
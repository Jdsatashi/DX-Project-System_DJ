# Generated by Django 5.0.3 on 2024-06-18 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_alter_user_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='device_token',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
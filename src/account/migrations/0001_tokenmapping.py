# Generated by Django 5.0.3 on 2024-05-15 02:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', 'migrate_susers'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('refresh_jti', models.CharField(max_length=255)),
                ('access_jti', models.CharField(max_length=255)),
                ('expired_at', models.DateTimeField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

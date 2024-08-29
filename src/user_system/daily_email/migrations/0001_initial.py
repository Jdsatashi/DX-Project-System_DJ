# Generated by Django 5.0.3 on 2024-08-23 11:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('email_type', models.CharField(max_length=255, unique=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserGetMail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_sent', models.DateTimeField(blank=True, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('email_detail', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_get_mail', to='daily_email.emaildetail')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_get_mail', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'email_detail')},
            },
        ),
    ]
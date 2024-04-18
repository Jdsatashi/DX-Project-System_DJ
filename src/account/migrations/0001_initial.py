# Generated by Django 5.0.3 on 2024-04-18 03:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('user_type', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.CharField(primary_key=True, serialize=False, unique=True)),
                ('username', models.CharField(blank=True, default=None, max_length=255, null=True, unique=True)),
                ('email', models.EmailField(blank=True, default=None, max_length=254, null=True)),
                ('phone_number', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('phone_number2', models.CharField(blank=True, default=None, max_length=24, null=True, unique=True)),
                ('password', models.CharField(max_length=512)),
                ('region', models.CharField(blank=True, default=None, max_length=100, null=True)),
                ('status', models.CharField(default=None, max_length=40, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('last_login', models.DateTimeField(blank=True, default=None, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('user_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='user_type.usertype', to_field='user_type')),
            ],
            options={
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='Perm',
            fields=[
                ('name', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('note', models.TextField(blank=True, default=None, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('object_id', models.CharField(max_length=255)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'db_table': 'users_perm',
            },
        ),
        migrations.CreateModel(
            name='GroupPerm',
            fields=[
                ('name', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('note', models.TextField(blank=True, default=None, null=True)),
                ('allow', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('perm', models.ManyToManyField(blank=True, to='account.perm')),
            ],
            options={
                'db_table': 'users_group_perm',
            },
        ),
        migrations.CreateModel(
            name='UserGroupPerm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allow', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.groupperm')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_user_group_perm',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='group_user',
            field=models.ManyToManyField(blank=True, related_name='users_rela', through='account.UserGroupPerm', to='account.groupperm'),
        ),
        migrations.CreateModel(
            name='UserPerm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allow', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('perm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.perm')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_user_perm',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='perm_user',
            field=models.ManyToManyField(blank=True, related_name='users_rela', through='account.UserPerm', to='account.perm'),
        ),
        migrations.CreateModel(
            name='Verify',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_verify', models.BooleanField(default=False)),
                ('verify_code', models.CharField(max_length=64)),
                ('verify_type', models.CharField(default=None, max_length=128)),
                ('device_code', models.CharField(max_length=255, null=True)),
                ('note', models.TextField(default=None, null=True)),
                ('verify_time', models.DateTimeField(null=True)),
                ('expired_at', models.DateTimeField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_verify',
            },
        ),
    ]

# Generated by Django 5.0.3 on 2024-03-14 03:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('user_type', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuyenHanUser',
            fields=[
                ('maQuyenHan', models.CharField(primary_key=True, serialize=False, unique=True)),
                ('tenQuyen', models.CharField(max_length=255, unique=True)),
                ('moTa', models.TextField(null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'users_quyenhan',
            },
        ),
        migrations.CreateModel(
            name='NhomUser',
            fields=[
                ('maNhom', models.CharField(primary_key=True, serialize=False, unique=True)),
                ('tenNhom', models.CharField(max_length=255)),
                ('moTa', models.TextField(null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('quyen', models.ManyToManyField(related_name='nhomUser', to='account.quyenhanuser')),
            ],
            options={
                'db_table': 'users_nhomuser',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('usercode', models.CharField(primary_key=True, serialize=False, unique=True)),
                ('username', models.CharField(max_length=255, null=True, unique=True)),
                ('email', models.EmailField(max_length=254, null=True, unique=True)),
                ('phone_number', models.CharField(max_length=15, null=True, unique=True)),
                ('khuVuc', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(max_length=40, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('loaiUser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='user_type.usertype', to_field='loaiUser')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('nhomUser', models.ManyToManyField(blank=True, related_name='users', to='account.nhomuser')),
                ('quyenUser', models.ManyToManyField(blank=True, related_name='users', to='account.quyenhanuser')),
            ],
            options={
                'db_table': 'users',
            },
        ),
    ]

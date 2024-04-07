# Generated by Django 5.0.3 on 2024-04-07 05:59

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
            name='NhomQuyen',
            fields=[
                ('name', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('mota', models.TextField(blank=True, default=None, null=True)),
                ('allow', models.BooleanField(default=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'users_nhom',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.CharField(primary_key=True, serialize=False, unique=True)),
                ('username', models.CharField(blank=True, default=None, max_length=255, null=True, unique=True)),
                ('email', models.EmailField(blank=True, default=None, max_length=254, null=True)),
                ('phone_number', models.CharField(blank=True, default=None, max_length=128, null=True)),
                ('password', models.CharField(max_length=256)),
                ('khuVuc', models.CharField(blank=True, default=None, max_length=100, null=True)),
                ('status', models.CharField(default=None, max_length=40, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('last_login', models.DateTimeField(blank=True, default=None, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('loaiUser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='user_type.usertype', to_field='loaiUser')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='NhomQuyenUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allow', models.BooleanField(default=True)),
                ('nhom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.nhomquyen')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_nhomQuyen_user',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='nhomUser',
            field=models.ManyToManyField(blank=True, related_name='users_rela', through='account.NhomQuyenUser', to='account.nhomquyen'),
        ),
        migrations.CreateModel(
            name='Quyen',
            fields=[
                ('name', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('mota', models.TextField(blank=True, default=None, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('object_id', models.CharField(max_length=255)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'db_table': 'users_quyen',
            },
        ),
        migrations.AddField(
            model_name='nhomquyen',
            name='quyen',
            field=models.ManyToManyField(blank=True, to='account.quyen'),
        ),
        migrations.CreateModel(
            name='QuyenUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allow', models.BooleanField(default=True)),
                ('quyen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.quyen')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_quyen_user',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='quyenUser',
            field=models.ManyToManyField(blank=True, related_name='users_rela', through='account.QuyenUser', to='account.quyen'),
        ),
        migrations.CreateModel(
            name='XacThuc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xac_thuc', models.BooleanField(default=False)),
                ('ma_xac_thuc', models.CharField(max_length=64)),
                ('loai_xac_thuc', models.CharField(default=None, max_length=128)),
                ('moTa', models.TextField(default=None, null=True)),
                ('time_xac_thuc', models.DateTimeField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_xac_thuc',
            },
        ),
    ]

# Generated by Django 5.0.3 on 2024-03-14 01:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('kh_nhomkh', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='KHProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenBanKe', models.CharField(max_length=255)),
                ('tenDoanhNghiep', models.CharField(max_length=255, null=True)),
                ('maNVTT', models.CharField(max_length=255, null=True)),
                ('diaChi', models.TextField(null=True)),
                ('nguoiLap', models.TextField(null=True)),
                ('maKHCap1', models.CharField(max_length=255, null=True)),
                ('maKH', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('maNhomKH', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kh_nhomkh.nhomkh')),
            ],
            options={
                'db_table': 'kh_profile',
            },
        ),
    ]

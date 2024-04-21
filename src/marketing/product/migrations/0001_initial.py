# Generated by Django 5.0.3 on 2024-04-21 05:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('company', 'migrate_old_company'),
    ]

    operations = [
        migrations.CreateModel(
            name='Producer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.CharField(max_length=12, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=24, null=True)),
                ('main_id', models.CharField(max_length=24, null=True)),
                ('created_by', models.CharField(max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.CharField(max_length=10, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'products_type',
            },
        ),
        migrations.CreateModel(
            name='RegistrationUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='UseFor',
            fields=[
                ('id', models.CharField(max_length=64, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='UseObject',
            fields=[
                ('id', models.CharField(max_length=64, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationCert',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('date_activated', models.DateField()),
                ('date_expired', models.DateField()),
                ('producer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.producer')),
                ('registered_unit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.registrationunit')),
            ],
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.CharField(max_length=12, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('ingredient', models.CharField(max_length=255)),
                ('amount', models.CharField(max_length=50)),
                ('poison_group', models.CharField(max_length=50)),
                ('amount_warning', models.IntegerField(default=0)),
                ('status', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='company.company')),
                ('product_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.producttype')),
                ('registration', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.registrationcert')),
            ],
        ),
        migrations.CreateModel(
            name='CategoryDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dosage', models.CharField(max_length=255)),
                ('usage', models.CharField(max_length=255)),
                ('cate_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.productcategory')),
                ('use_for', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.usefor')),
                ('use_object', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.useobject')),
            ],
        ),
    ]

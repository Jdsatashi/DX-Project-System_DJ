# Generated by Django 5.0.3 on 2024-05-06 08:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('price_list', '0001_initial'),
        ('product', 'migrate_old_product'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.CharField(max_length=24, primary_key=True, serialize=False)),
                ('date_get', models.DateField(null=True)),
                ('date_company_get', models.DateTimeField(null=True)),
                ('date_delay', models.IntegerField(default=0)),
                ('list_type', models.CharField(max_length=24, null=True)),
                ('is_so', models.BooleanField(default=False, null=True)),
                ('id_so', models.CharField(default=None, max_length=255, null=True)),
                ('id_offer_consider', models.CharField(default=None, max_length=255, null=True)),
                ('created_by', models.CharField(max_length=64, null=True)),
                ('note', models.CharField(max_length=255, null=True)),
                ('status', models.CharField(max_length=24, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('price_list_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_price_list', to='price_list.pricelist')),
            ],
        ),
        migrations.CreateModel(
            name='OrderDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_quantity', models.IntegerField(default=1)),
                ('order_box', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('point_per_box', models.DecimalField(decimal_places=2, max_digits=8, null=True)),
                ('price_list_so', models.DecimalField(decimal_places=0, max_digits=10, null=True)),
                ('order_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_detail', to='order.order')),
                ('product_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_product', to='product.product')),
            ],
        ),
    ]

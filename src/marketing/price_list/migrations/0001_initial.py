# Generated by Django 5.0.3 on 2024-06-23 02:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('livestream', '0001_initial'),
        ('product', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceList',
            fields=[
                ('id', models.CharField(max_length=12, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('date_start', models.DateField()),
                ('date_end', models.DateField()),
                ('note', models.CharField(blank=True, max_length=255, null=True)),
                ('type', models.CharField(choices=[('main', 'main'), ('sub', 'sub')], default='sub', max_length=64)),
                ('status', models.CharField(max_length=24, null=True)),
                ('created_by', models.CharField(blank=True, max_length=64, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='PointOfSeason',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('point', models.FloatField(blank=True, default=0, null=True)),
                ('total_point', models.FloatField(blank=True, default=0, null=True)),
                ('used_point', models.FloatField(blank=True, default=0, null=True)),
                ('bonus_point', models.FloatField(blank=True, default=0, null=True)),
                ('redundant', models.FloatField(blank=True, default=0, null=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('price_list', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='price_list.pricelist')),
            ],
        ),
        migrations.CreateModel(
            name='ProductPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.BigIntegerField()),
                ('quantity_in_box', models.IntegerField(default=0)),
                ('point', models.FloatField(blank=True, null=True)),
                ('price_list', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='price_list.pricelist')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.product')),
            ],
        ),
        migrations.AddField(
            model_name='pricelist',
            name='products',
            field=models.ManyToManyField(through='price_list.ProductPrice', to='product.product'),
        ),
        migrations.CreateModel(
            name='SpecialOffer',
            fields=[
                ('id', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('time_start', models.DateTimeField(null=True)),
                ('time_end', models.DateTimeField(null=True)),
                ('type_list', models.CharField(default='manual', max_length=24)),
                ('count_turnover', models.BooleanField(default=False)),
                ('target', models.BigIntegerField(default=0)),
                ('quantity_can_use', models.FloatField(null=True)),
                ('box_can_use', models.IntegerField(null=True)),
                ('status', models.CharField(max_length=24, null=True)),
                ('note', models.CharField(max_length=255, null=True)),
                ('created_by', models.CharField(blank=True, max_length=64, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('live_stream', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='offers', to='livestream.livestream')),
            ],
        ),
        migrations.CreateModel(
            name='SpecialOfferProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.BigIntegerField(null=True)),
                ('point', models.FloatField(null=True)),
                ('quantity_in_box', models.IntegerField(default=0)),
                ('cashback', models.BigIntegerField(null=True)),
                ('max_order_box', models.IntegerField(null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='special_offers', to='product.product')),
                ('special_offer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='special_offers', to='price_list.specialoffer')),
            ],
        ),
        migrations.AddField(
            model_name='specialoffer',
            name='product',
            field=models.ManyToManyField(through='price_list.SpecialOfferProduct', to='product.product'),
        ),
    ]

# Generated by Django 5.0.3 on 2024-05-14 13:09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_list', '0002_alter_productprice_point_alter_productprice_price'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PointOfSeason',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('point', models.FloatField(blank=True, default=0, null=True)),
                ('total_point', models.FloatField(blank=True, default=0, null=True)),
                ('used_point', models.FloatField(blank=True, default=0, null=True)),
                ('bonus_point', models.FloatField(blank=True, default=0, null=True)),
                ('redundant', models.FloatField(blank=True, default=0, null=True)),
                ('price_list', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='price_list.pricelist')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

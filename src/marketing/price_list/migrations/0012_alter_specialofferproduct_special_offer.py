# Generated by Django 5.0.3 on 2024-05-20 03:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_list', '0011_remove_specialofferproduct_quantity_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specialofferproduct',
            name='special_offer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='special_offers', to='price_list.specialoffer'),
        ),
    ]
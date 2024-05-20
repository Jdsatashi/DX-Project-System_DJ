# Generated by Django 5.0.3 on 2024-05-20 08:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_remove_orderdetail_point_per_box_order_order_point_and_more'),
        ('price_list', '0013_alter_specialofferproduct_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='new_special_offer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='price_list.specialoffer'),
        ),
    ]

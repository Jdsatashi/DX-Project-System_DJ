# Generated by Django 5.0.3 on 2024-10-21 01:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0011_alter_order_new_special_offer_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='id_offer_consider',
        ),
        migrations.RemoveField(
            model_name='order',
            name='id_so',
        ),
        migrations.AddField(
            model_name='order',
            name='count_turnover',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='order',
            name='minus_so_box',
            field=models.BigIntegerField(default=None, null=True),
        ),
    ]

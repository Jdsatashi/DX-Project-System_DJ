# Generated by Django 5.0.3 on 2024-09-11 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0009_rename_price_list_so_orderdetail_price_so'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='npp_id',
            field=models.CharField(max_length=64, null=True),
        ),
    ]
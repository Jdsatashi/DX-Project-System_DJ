# Generated by Django 5.0.3 on 2024-05-19 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_list', '0006_rename_quantity_specialofferproduct_quantity_in_box_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specialoffer',
            name='type_list',
            field=models.CharField(default='manual', max_length=24),
        ),
    ]

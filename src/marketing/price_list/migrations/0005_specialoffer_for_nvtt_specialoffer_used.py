# Generated by Django 5.0.3 on 2024-08-11 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_list', '0004_delete_pointofseason'),
    ]

    operations = [
        migrations.AddField(
            model_name='specialoffer',
            name='for_nvtt',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='specialoffer',
            name='used',
            field=models.BooleanField(default=False),
        ),
    ]

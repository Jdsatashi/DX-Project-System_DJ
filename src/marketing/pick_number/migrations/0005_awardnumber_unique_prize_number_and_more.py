# Generated by Django 5.0.3 on 2024-09-20 23:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pick_number', '0004_remove_eventnumber_point_exchange_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='awardnumber',
            constraint=models.UniqueConstraint(fields=('prize', 'number'), name='unique_prize_number'),
        ),
        migrations.AddConstraint(
            model_name='awardnumber',
            constraint=models.UniqueConstraint(fields=('prize', 'turn_roll'), name='unique_prize_turn_roll'),
        ),
    ]

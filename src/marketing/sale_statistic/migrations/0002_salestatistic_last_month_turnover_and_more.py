# Generated by Django 5.0.3 on 2024-08-09 02:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sale_statistic', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='salestatistic',
            name='last_month_turnover',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='salestatistic',
            name='minus_turnover',
            field=models.BigIntegerField(default=0),
        ),
    ]
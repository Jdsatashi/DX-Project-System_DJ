# Generated by Django 5.0.3 on 2024-08-08 02:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system_func', '0001_initial'),
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
                ('period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='season_point', to='system_func.periodseason')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='season_point', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

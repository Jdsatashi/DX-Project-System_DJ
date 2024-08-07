# Generated by Django 5.0.3 on 2024-08-07 04:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_remove_user_device_token_phonenumber_device_code_and_more'),
        ('order', '0007_alter_seasonalstatistic_type'),
        ('pick_number', '0003_userjoinevent_phone_prizeevent_awardnumber'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventnumber',
            name='point_exchange',
        ),
        migrations.RemoveField(
            model_name='eventnumber',
            name='price_list',
        ),
        migrations.RemoveField(
            model_name='userjoinevent',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='userjoinevent',
            name='used_point',
        ),
        migrations.AddField(
            model_name='awardnumber',
            name='turn_roll',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='eventnumber',
            name='date_result',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='eventnumber',
            name='table_point',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='event_number', to='order.seasonalstatistic'),
        ),
        migrations.AddField(
            model_name='userjoinevent',
            name='turn_per_point',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='userjoinevent',
            name='turn_pick',
            field=models.IntegerField(null=True),
        ),
        migrations.CreateModel(
            name='PickNumberLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('action', models.CharField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pick_number_log', to='pick_number.eventnumber')),
                ('phone', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pick_number_log', to='account.phonenumber')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pick_number_log', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

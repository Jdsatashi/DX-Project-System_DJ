# Generated by Django 5.0.3 on 2024-05-29 04:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pick_number', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userjoinevent',
            name='number',
        ),
        migrations.AlterField(
            model_name='userjoinevent',
            name='id',
            field=models.CharField(editable=False, max_length=32, primary_key=True, serialize=False, unique=True),
        ),
        migrations.CreateModel(
            name='NumberSelected',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('number', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='number_selected', to='pick_number.numberlist')),
                ('user_event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='number_selected', to='pick_number.userjoinevent')),
            ],
        ),
    ]

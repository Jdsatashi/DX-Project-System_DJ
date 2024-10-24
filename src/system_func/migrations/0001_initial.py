# Generated by Django 5.0.3 on 2024-08-08 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PeriodSeason',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_date', models.DateField()),
                ('to_date', models.DateField()),
                ('type', models.CharField(max_length=24)),
                ('period', models.CharField(choices=[('current', 'hiện tại'), ('previous', 'mùa trước'), ('past', 'mùa cũ')], max_length=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]

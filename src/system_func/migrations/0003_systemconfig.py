# Generated by Django 5.0.3 on 2024-10-11 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system_func', '0002_pointofseason'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, null=True)),
                ('value', models.TextField(null=True)),
                ('note', models.TextField(null=True)),
            ],
        ),
    ]

# Generated by Django 5.0.3 on 2024-05-10 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client_profile', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientprofile',
            name='dob',
            field=models.DateField(null=True),
        ),
    ]

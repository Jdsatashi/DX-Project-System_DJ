# Generated by Django 5.0.3 on 2024-04-02 03:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nv_profile', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='nvchucdanh',
            old_name='moTa',
            new_name='mota',
        ),
        migrations.RenameField(
            model_name='nvphongban',
            old_name='moTa',
            new_name='mota',
        ),
    ]

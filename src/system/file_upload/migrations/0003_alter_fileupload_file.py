# Generated by Django 5.0.3 on 2024-06-25 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file_upload', '0002_alter_fileupload_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fileupload',
            name='file',
            field=models.FileField(max_length=255, unique=True, upload_to=''),
        ),
    ]

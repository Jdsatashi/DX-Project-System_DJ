# Generated by Django 5.0.3 on 2024-04-16 14:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(unique=True, upload_to='')),
                ('file_name', models.CharField(blank=True, max_length=255, unique=True)),
                ('file_ext', models.CharField(blank=True, max_length=12)),
                ('type', models.CharField(choices=[('document', 'Document'), ('image', 'Image')], max_length=8, null=True)),
                ('order', models.IntegerField(default=1)),
                ('note', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ContentFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='file_upload.fileupload', to_field='file')),
            ],
        ),
    ]

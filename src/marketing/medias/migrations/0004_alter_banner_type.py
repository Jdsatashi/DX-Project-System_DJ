# Generated by Django 5.0.3 on 2024-06-30 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medias', '0003_rename_url_banneritem_direct_url_banner_display_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='banner',
            name='type',
            field=models.CharField(max_length=64, null=True),
        ),
    ]
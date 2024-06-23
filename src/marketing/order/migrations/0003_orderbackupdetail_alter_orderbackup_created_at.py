# Generated by Django 5.0.3 on 2024-06-23 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderBackupDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=255, null=True)),
                ('product_id', models.CharField(max_length=255, null=True)),
                ('order_quantity', models.IntegerField(default=1)),
                ('order_box', models.FloatField(default=0)),
                ('product_price', models.BigIntegerField(null=True)),
                ('quantity_in_box', models.IntegerField(null=True)),
                ('point_get', models.FloatField(null=True)),
                ('price_list_so', models.FloatField(null=True)),
                ('note', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='orderbackup',
            name='created_at',
            field=models.DateTimeField(null=True),
        ),
    ]

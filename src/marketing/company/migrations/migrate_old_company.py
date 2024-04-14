from django.db import migrations

from marketing.company.models import Company
from utils.constants import old_data
from utils.helpers import table_data


def add_old_company(apps, schema_editor):
    data = table_data(old_data['tb_congty'])
    for k, v in enumerate(data):
        try:
            Company.objects.create(id=v[0], name=v[1], note=v[2], color_code=v[5], created_at=v[3])
            print(f"Added company {v[1]} - {v[0]}")
        except Exception as e:
            print(f"----- ERROR -----")
            print(f"Message: Error when adding company.")
            print(e)
            raise Exception(e)


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_old_company),
    ]

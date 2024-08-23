from django.db import migrations

from user_system.daily_email.models import EmailDetail


def create_auto_mail(_, __):
    detail, _ = EmailDetail.objects.get_or_create(
        name='báo cáo toa mỗi ngày',
        email_type='report_order',
        defaults={'description': 'Báo cáo các toa thuốc phát sinh trong ngày'}
    )


class Migration(migrations.Migration):
    dependencies = [('daily_email', '0001_initial')]

    operations = [
        migrations.RunPython(create_auto_mail),
    ]

import os
from datetime import datetime, timedelta, time
import django

from celery import Celery, shared_task
from django.conf import settings

from app.logs import app_log

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

app_celery = Celery('projects')

app_celery.config_from_object('django.conf:settings', namespace='CELERY')

app_celery.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app_celery.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@shared_task
def send_daily_email_task():
    from app.tasks.report_mail import send_daily_email

    last_date = datetime.now().date() - timedelta(days=1)
    app_log.info(f"Date analysis: {last_date}")
    # - timedelta(days=1)
    send_daily_email(last_date)


@shared_task
def send_daily_nvtt_email_task():
    from app.tasks.report_mail import send_daily_nvtt_email

    last_date = datetime.now().date() - timedelta(days=1)
    app_log.info(f"Date analysis: {last_date}")
    send_daily_nvtt_email(last_date)

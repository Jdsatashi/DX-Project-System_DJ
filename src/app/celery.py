import os
from datetime import datetime, timedelta
import django

from celery import Celery, shared_task
from django.conf import settings


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

    today = datetime.now().date()   # - timedelta(days=1)
    send_daily_email(today)

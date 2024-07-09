import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app_celery = Celery('projects')

app_celery.config_from_object('django.conf:settings', namespace='CELERY')

app_celery.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app_celery.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

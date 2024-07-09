from celery import Celery

app_celery = Celery('app')

app_celery.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app_celery.autodiscover_tasks()


@app_celery.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

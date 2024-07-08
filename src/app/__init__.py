from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from app.celery import app_celery

__all__ = ('app_celery',)

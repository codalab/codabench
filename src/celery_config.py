from celery import Celery

app = Celery()

from django.conf import settings  # noqa

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

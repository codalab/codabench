from celery import Celery
from kombu import Queue, Exchange

app = Celery()

from django.conf import settings  # noqa

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.task_queues = [
    # Mostly defining queue here so we can set x-max-priority
    Queue('compute-worker', Exchange('compute-worker'), routing_key='compute-worker', queue_arguments={'x-max-priority': 10}),
]

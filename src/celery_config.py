from celery import Celery
from kombu import Queue, Exchange
from django.conf import settings
import urllib.parse
import copy

app = Celery()

from django.conf import settings  # noqa

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.task_queues = [
    # Mostly defining queue here so we can set x-max-priority
    Queue('compute-worker', Exchange('compute-worker'), routing_key='compute-worker', queue_arguments={'x-max-priority': 10}),
]

_vhost_apps = {}


def app_for_vhost(vhost):
    # Function to get the app for a vhost
    if vhost not in _vhost_apps:
        # Take the CELERY_BROKER_URL and replace the vhost with the vhhost for this queue
        broker_url = settings.CELERY_BROKER_URL
        # This is require to work around https://bugs.python.org/issue18828
        scheme = urllib.parse.urlparse(broker_url).scheme
        urllib.parse.uses_relative.append(scheme)
        urllib.parse.uses_netloc.append(scheme)
        broker_url = urllib.parse.urljoin(broker_url, vhost)
        vhost_app = Celery()
        # Copy the settings so we can modify the broker url to include the vhost
        django_settings = copy.copy(settings)
        django_settings.CELERY_BROKER_URL = broker_url
        vhost_app.config_from_object(django_settings, namespace='CELERY')
        vhost_app.conf.task_queues = app.conf.task_queues
        _vhost_apps[vhost] = vhost_app
    return _vhost_apps[vhost]

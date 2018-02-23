from celery import Celery
import os

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')

app = Celery()

# Load settings from Django first
app.config_from_object('django.conf:settings', namespace='CELERY')

# Final set of settings
app.conf.update(
    broker_url='amqp://guest:guest@rabbitmq:5672//',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)

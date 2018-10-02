import os


BROKER_URL = os.environ.get('BROKER_URL')
BROKER_USE_SSL = os.environ.get('BROKER_USE_SSL', False)
CELERY_IMPORTS = ('worker',)
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ('json',)

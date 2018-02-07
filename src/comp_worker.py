from celery import Celery

# set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

app = Celery('comps')

# from django.conf import settings  # noqa
#
app.config_from_object('django.conf:settings')
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# @app.task(bind=True)
# def smoke(self, x):
#     print('Request: {0!r}'.format(self.request))
#     return x

# print("BROKER=", app.conf['BROKER_URL'], file=sys.stderr)
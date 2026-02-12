from settings.base import *  # noqa: F401,F403
# these noqa comments are for flake8 ignores

DEBUG = True

CELERY_TASK_ALWAYS_EAGER = True

# Don't use whitenoise -- so we don't get exceptions for missing files

STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}
# NOTE! We cannot use in memory databases at the moment with Channels. If we remove channels,
# we can turn this back on:
#     # Use in memory database
#     DATABASES['default'] = {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': ':memory:',
#     }

# Must override this so djdt doesn't screw up tests
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: False
}
IS_TESTING = True

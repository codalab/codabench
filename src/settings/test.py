from settings.base import *
import os

DEBUG = True

CELERY_TASK_ALWAYS_EAGER = True

# Don't use whitenoise -- so we don't get exceptions for missing files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Use in memory database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

# Must override this so djdt doesn't screw up tests
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: False
}

SELENIUM_HOSTNAME = os.environ.get("SELENIUM_HOSTNAME", "localhost")

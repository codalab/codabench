from settings.base import *  # noqa: F401,F403


# Don't use whitenoise -- so we don't get exceptions for missing files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Use in memory database
DATABASES['default'] = {  # noqa: F405
    'ENGINE': 'django.db.backends.sqlite3',
}

# Must override this so djdt doesn't screw up tests
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: False
}

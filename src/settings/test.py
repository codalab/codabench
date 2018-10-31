from settings.base import *  # noqa: F401,F403


# Don't use whitenoise -- so we don't get exceptions for missing files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Use in memory database
DATABASES['default'] = {  # noqa: F405
    'ENGINE': 'django.db.backends.sqlite3',
}

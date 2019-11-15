import os

from .base import *


ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(",")

STATICFILES_STORAGE = 'utils.storage.WhiteNoiseStaticFilesStorage'

CORS_ORIGIN_ALLOW_ALL = False

from .base import *  # noqa: F401,F403


ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(",")

# Use our own storage that ignores missing staticfiles
STATICFILES_STORAGE = 'utils.storage.WhiteNoiseStaticFilesStorage'

CORS_ORIGIN_ALLOW_ALL = False
DEBUG = False

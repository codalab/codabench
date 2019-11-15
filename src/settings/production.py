from .base import *  # noqa: F401,F403


ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(",")

# Use our own storage that ignores missing staticfiles
STATICFILES_STORAGE = 'utils.storage.WhiteNoiseStaticFilesStorage'

CORS_ORIGIN_ALLOW_ALL = False
DEBUG = False

# =========================================================================
# Email
# =========================================================================
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.environ.get('EMAIL_PORT', 587)
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', True)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'CodaLab <noreply@codalab.org>')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'noreply@codalab.org')

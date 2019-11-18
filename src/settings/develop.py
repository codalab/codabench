from settings.base import *  # noqa: F401,F403

# =============================================================================
# Whitenoise
# =============================================================================
INSTALLED_APPS += ('whitenoise',)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MIDDLEWARE += ('whitenoise.middleware.WhiteNoiseMiddleware',)

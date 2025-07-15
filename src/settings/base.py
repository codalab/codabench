import os
import sys
from datetime import timedelta
from celery.schedules import crontab

import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Also add ../../apps to python path
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# =============================================================================
# Django
# =============================================================================
ALLOWED_HOSTS = ['*']
USE_X_FORWARDED_HOST = True

SITE_ID = 1

SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'http://localhost')
DOMAIN_NAME = os.environ.get('DOMAIN_NAME', 'localhost').split(':')[0]

THIRD_PARTY_APPS = (
    'django_su',  # Must come before django.contrib.admin
    'ajax_select',  # For django_su

    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django.contrib.humanize',

    'rest_framework',
    'rest_framework.authtoken',
    'oauth2_provider',
    # 'corsheaders',
    'social_django',
    'django_extensions',
    'django_filters',
    'storages',
    'channels',
    'drf_yasg',
    'redis',
)
OUR_APPS = (
    'chahub',
    'analytics',
    'competitions',
    'datasets',
    'pages',
    'profiles',
    'leaderboards',
    'tasks',
    'commands',
    'queues',
    'health',
    'forums',
    'announcements',
    'oidc_configurations',
)
INSTALLED_APPS = THIRD_PARTY_APPS + OUR_APPS

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'corsheaders.middleware.CorsMiddleware', # BB
    'django.middleware.common.CommonMiddleware'
)

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'utils.context_processors.common_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
SECRET_KEY = os.environ.get("SECRET_KEY", '(*0&74%ihg0ui+400+@%2pe92_c)x@w2m%6s(jhs^)dc$&&g93')
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# =============================================================================
# Authentication
# =============================================================================
AUTHENTICATION_BACKENDS = (
    'social_core.backends.github.GithubOAuth2',
    'utils.oauth_backends.ChahubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
    'django_su.backends.SuBackend',
    'profiles.backends.EmailAuthenticationBackend',
)

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    # 'social_core.pipeline.user.user_details',
    'social_core.pipeline.social_auth.associate_by_email',
    'profiles.pipeline.user_details',
)

# Github
SOCIAL_AUTH_GITHUB_KEY = os.environ.get('SOCIAL_AUTH_GITHUB_KEY')
SOCIAL_AUTH_GITHUB_SECRET = os.environ.get('SOCIAL_AUTH_GITHUB_SECRET')
SOCIAL_AUTH_GITHUB_SCOPE = ['user']

# Codalab Example settings
SOCIAL_AUTH_CHAHUB_BASE_URL = os.environ.get('SOCIAL_AUTH_CHAHUB_BASE_URL', 'asdfasdfasfd')
SOCIAL_AUTH_CHAHUB_KEY = os.environ.get('SOCIAL_AUTH_CHAHUB_KEY', 'asdfasdfasfd')
SOCIAL_AUTH_CHAHUB_SECRET = os.environ.get('SOCIAL_AUTH_CHAHUB_SECRET', 'asdfasdfasfdasdfasdf')

# Generic
SOCIAL_AUTH_STRATEGY = 'social_django.strategy.DjangoStrategy'
SOCIAL_AUTH_STORAGE = 'social_django.models.DjangoStorage'
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ['username', 'first_name', 'email']

# User Models
AUTH_USER_MODEL = 'profiles.User'
SOCIAL_AUTH_USER_MODEL = 'profiles.User'

# =============================================================================
# Debugging
# =============================================================================
DEBUG = os.environ.get("DEBUG", False)

# =============================================================================
# Database
# =============================================================================
DATABASES = {'default': {}}

db_from_env = dj_database_url.config()
if db_from_env:
    DATABASES['default'].update(db_from_env)
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ.get('DB_NAME', 'postgres'),
            'USER': os.environ.get('DB_USERNAME', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'db'),
            'PORT': 5432
        }
    }

# TODO: Pull this, leaving in case django-oauth-toolkit problems
# # =============================================================================
# # SSL
# # =============================================================================
# if os.environ.get('USE_SSL'):
#     SECURE_SSL_REDIRECT = True
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# else:
#     # Allows us to use with django-oauth-toolkit on localhost sans https
#     SESSION_COOKIE_SECURE = False

# =========================================================================
# RabbitMQ
# =========================================================================
RABBITMQ_DEFAULT_USER = os.environ.get('RABBITMQ_DEFAULT_USER', 'guest')
RABBITMQ_DEFAULT_PASS = os.environ.get('RABBITMQ_DEFAULT_PASS', 'guest')
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbit')
RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
RABBITMQ_MANAGEMENT_PORT = os.environ.get('RABBITMQ_MANAGEMENT_PORT', '15672')
RABBITMQ_SCHEME = os.environ.get('RABBITMQ_SCHEME', 'http')
RABBITMQ_PYRABBIT_URL = None  # used in Heroku settings, mainly
FLOWER_HOST = os.environ.get('FLOWER_HOST', RABBITMQ_HOST)
FLOWER_PUBLIC_PORT = os.environ.get('FLOWER_PUBLIC_PORT', '5555')

# ============================================================================
# Celery
# ============================================================================
CELERY_BROKER_USE_SSL = os.environ.get('BROKER_USE_SSL', False)
CELERY_BROKER_URL = os.environ.get('BROKER_URL')
if not CELERY_BROKER_URL:
    CELERY_BROKER_URL = f'pyamqp://{RABBITMQ_DEFAULT_USER}:{RABBITMQ_DEFAULT_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}//'
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://redis:6379")
CELERY_IGNORE_RESULT = False      # Ensure that Celery tracks the state
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ('json',)
CELERY_BEAT_SCHEDULE = {
    'do_phase_migrations': {
        'task': 'competitions.tasks.do_phase_migrations',
        'schedule': timedelta(seconds=300),
    },
    'update_phase_statuses': {
        'task': 'competitions.tasks.update_phase_statuses',
        'schedule': timedelta(seconds=3600)
    },
    'submission_status_cleanup': {
        'task': 'competitions.tasks.submission_status_cleanup',
        'schedule': timedelta(seconds=3600)
    },
    'create_storage_analytics_snapshot': {
        'task': 'analytics.tasks.create_storage_analytics_snapshot',
        'schedule': crontab(hour='2', minute='0', day_of_week='sun')  # Every Sunday at 02:00 UTC time
    },
    'update_home_page_counters': {
        'task': 'analytics.tasks.update_home_page_counters',
        'schedule': timedelta(days=1),  # Run every 24 hours
    },
    'clean_deleted_users': {
        'task': 'profiles.tasks.clean_deleted_users',
        'schedule': timedelta(days=1),  # Run every 24 hours
    },
    'clean_non_activated_users': {
        'task': 'profiles.tasks.clean_non_activated_users',
        'schedule': timedelta(days=1),  # Run every 24 hours
    },
}
CELERY_TIMEZONE = 'UTC'
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# ============================================================================
# Caching
# ============================================================================
CACHES = {
    'default': {
        "BACKEND": "django_redis.cache.RedisCache",
        'LOCATION': [os.environ.get("REDIS_URL", "redis://redis:6379")],
        'OPTIONS': {
            "CONNECTION_POOL_KWARGS": {
                "max_connections": os.environ.get("REDIS_MAX_CONNECTIONS", 20),
                "retry_on_timeout": True
            },
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}
REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15,
}

# =============================================================================
# DRF
# =============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DATETIME_INPUT_FORMATS': (
        'iso-8601',
        '%B %d, %Y',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        "rest_framework.renderers.JSONRenderer",
        "api.renderers.CustomBrowsableAPIRenderer")
}
# OAuth Toolkit
OAUTH2_PROVIDER = {
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'groups': 'Access to your groups'}
}

# =============================================================================
# OAuth
# =============================================================================
CORS_ORIGIN_ALLOW_ALL = True


# =============================================================================
# Logging
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

# =============================================================================
# Channels
# =============================================================================
ASGI_APPLICATION = "routing.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://redis:6379")],

            # To hold large submission outputs
            "capacity": 1500,  # default 100
        },
        # "ROUTING": "ProblemSolverCentral.routing.channel_routing",
    },
}

SUBMISSIONS_API_URL = os.environ.get('SUBMISSIONS_API_URL', "http://django/api")
MAX_EXECUTION_TIME_LIMIT = os.environ.get('MAX_EXECUTION_TIME_LIMIT', "600")  # time limit of the default queue

# =============================================================================
# Storage
# =============================================================================
STORAGE_TYPE = os.environ.get('STORAGE_TYPE', 's3').lower()
DEFAULT_FILE_STORAGE = None  # defined based on STORAGE_TYPE selection

TEMP_SUBMISSION_STORAGE = os.environ.get('TEMP_SUBMISSION_STORAGE', '/codalab_tmp')

# Make sure storage exists
if not os.path.exists(TEMP_SUBMISSION_STORAGE):
    os.makedirs(TEMP_SUBMISSION_STORAGE)

STORAGE_IS_S3 = STORAGE_TYPE == 's3' or STORAGE_TYPE == 'minio'
STORAGE_IS_GCS = STORAGE_TYPE == 'gcs'
STORAGE_IS_AZURE = STORAGE_TYPE == 'azure'

if STORAGE_IS_S3:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
elif STORAGE_IS_GCS:
    DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
elif STORAGE_IS_AZURE:
    DEFAULT_FILE_STORAGE = "utils.storage.CodalabAzureStorage"
else:
    raise NotImplementedError("Must use STORAGE_TYPE of 's3', 'minio', 'gcs', or 'azure'")

# Helpers to verify storage configuration
if STORAGE_IS_GCS:
    assert os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'), "Google Cloud Storage credentials are stored in a json " \
                                                             "file which GOOGLE_APPLICATION_CREDENTIALS env var " \
                                                             "should point to (edit in .env)"

FILE_UPLOAD_HANDLERS = ("django.core.files.uploadhandler.TemporaryFileUploadHandler",)

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = '/media/'

# S3 from AWS
S3_USE_SIGV4 = os.environ.get("S3_USE_SIGV4", True)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_STORAGE_PRIVATE_BUCKET_NAME = os.environ.get('AWS_STORAGE_PRIVATE_BUCKET_NAME')
AWS_S3_CALLING_FORMAT = os.environ.get('AWS_S3_CALLING_FORMAT', 'boto.s3.connection.OrdinaryCallingFormat')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', '')
AWS_DEFAULT_ACL = None  # Uses buckets security access policies
AWS_QUERYSTRING_AUTH = os.environ.get(
    # This stops signature/auths from appearing in saved URLs
    'AWS_QUERYSTRING_AUTH',
    False
)
if isinstance(AWS_QUERYSTRING_AUTH, str) and 'false' in AWS_QUERYSTRING_AUTH.lower():
    AWS_QUERYSTRING_AUTH = False  # Was set to string, convert to bool

# Azure
AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY')
AZURE_CONTAINER = os.environ.get('AZURE_CONTAINER', 'public')
BUNDLE_AZURE_ACCOUNT_NAME = os.environ.get('BUNDLE_AZURE_ACCOUNT_NAME', AZURE_ACCOUNT_NAME)
BUNDLE_AZURE_ACCOUNT_KEY = os.environ.get('BUNDLE_AZURE_ACCOUNT_KEY', AZURE_ACCOUNT_KEY)
BUNDLE_AZURE_CONTAINER = os.environ.get('BUNDLE_AZURE_CONTAINER', 'bundles')

# Google Cloud Storage
GS_PUBLIC_BUCKET_NAME = os.environ.get('GS_PUBLIC_BUCKET_NAME')
GS_PRIVATE_BUCKET_NAME = os.environ.get('GS_PRIVATE_BUCKET_NAME')
GS_BUCKET_NAME = GS_PUBLIC_BUCKET_NAME  # Default bucket set to public bucket

# Quota
DEFAULT_USER_QUOTA = 15  # 15GB


# =============================================================================
# Debug
# =============================================================================
if DEBUG:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE = ('debug_toolbar.middleware.DebugToolbarMiddleware',
                  'querycount.middleware.QueryCountMiddleware',
                  ) + MIDDLEWARE  # we want Debug Middleware at the top
    # tricks to have debug toolbar when developing with docker

    INTERNAL_IPS = ['127.0.0.1']

    import socket

    try:
        INTERNAL_IPS.append(socket.gethostbyname(socket.gethostname())[:-1])
    except socket.gaierror:
        pass

    QUERYCOUNT = {
        'IGNORE_REQUEST_PATTERNS': [
            r'^/admin/',
            r'^/static/',
        ]
    }

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True
    }

# =========================================================================
# Email
# =========================================================================
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.environ.get('EMAIL_PORT', 587)
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', True)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Codabench <noreply@codabench.org>')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'noreply@codabench.org')

# =============================================================================
# Chahub
# =============================================================================
CHAHUB_API_URL = os.environ.get('CHAHUB_API_URL')
CHAHUB_API_KEY = os.environ.get('CHAHUB_API_KEY')
CHAHUB_PRODUCER_ID = os.environ.get('CHAHUB_PRODUCER_ID')


# Django-Su (User impersonation)
SU_LOGIN_CALLBACK = 'profiles.admin.su_login_callback'
AJAX_LOOKUP_CHANNELS = {'django_su': dict(model='profiles.User', search_field='username')}

# =============================================================================
# Limit for re-running submission
# This is used to limit users to rerun submissions
# on default queue when number of submissions are < RERUN_SUBMISSION_LIMIT
# =============================================================================
RERUN_SUBMISSION_LIMIT = os.environ.get('RERUN_SUBMISSION_LIMIT', 30)


# =============================================================================
# Enable or disbale regular email sign-in an sign-up
# =============================================================================
ENABLE_SIGN_UP = os.environ.get('ENABLE_SIGN_UP', 'True').lower() == 'true'
ENABLE_SIGN_IN = os.environ.get('ENABLE_SIGN_IN', 'True').lower() == 'true'

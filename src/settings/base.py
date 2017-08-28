import os
import sys

from django.core.files.storage import get_storage_class


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Also add ../../apps to python path
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# =============================================================================
# Django
# =============================================================================
ALLOWED_HOSTS = ['*']
USE_X_FORWARDED_HOST = True

SITE_ID = 1

THIRD_PARTY_APPS = (
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    'rest_framework',
    'rest_framework_swagger',
    'whitenoise',
    'django_elasticsearch_dsl',
)
OUR_APPS = (
    'competitions',
    'datasets',
    'pages',
)
INSTALLED_APPS = THIRD_PARTY_APPS + OUR_APPS

MIDDLEWARE_CLASSES = (
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
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

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

DEFAULT_FROM_EMAIL = 'Do Not Reply <donotreply@imagefirstuniforms.com>'
SERVER_EMAIL = 'Do Not Reply <donotreply@imagefirstuniforms.com>'

LOGIN_REDIRECT_URL = '/'

# AUTH_USER_MODEL = 'profiles.User'


# =============================================================================
# Debugging
# =============================================================================

DEBUG = os.environ.get('DEBUG', True)


# =============================================================================
# Database
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite'),
        'CONN_MAX_AGE': 500,
    }
}


# =============================================================================
# DRF
# =============================================================================


# =============================================================================
# Search
# =============================================================================
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'localhost:9200'
    },
}


# =============================================================================
# Storage
# =============================================================================
DEFAULT_FILE_STORAGE = os.environ.get('DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage')

# S3 from AWS
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_STORAGE_PRIVATE_BUCKET_NAME = os.environ.get('AWS_STORAGE_PRIVATE_BUCKET_NAME')
AWS_S3_CALLING_FORMAT = os.environ.get('AWS_S3_CALLING_FORMAT', 'boto.s3.connection.OrdinaryCallingFormat')
AWS_S3_HOST = os.environ.get('AWS_S3_HOST', 's3-us-west-2.amazonaws.com')
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

# Helper booleans
STORAGE_IS_AWS = DEFAULT_FILE_STORAGE == 'storages.backends.s3boto.S3BotoStorage'
STORAGE_IS_AZURE = DEFAULT_FILE_STORAGE == 'storages.backends.azure_storage.AzureStorage'
STORAGE_IS_LOCAL = DEFAULT_FILE_STORAGE == 'django.core.files.storage.FileSystemStorage'

# Setup actual storage classes we use on the project
StorageClass = get_storage_class(DEFAULT_FILE_STORAGE)

if STORAGE_IS_AWS:
    BundleStorage = StorageClass(bucket=AWS_STORAGE_PRIVATE_BUCKET_NAME)
    PublicStorage = StorageClass(bucket=AWS_STORAGE_BUCKET_NAME)
elif STORAGE_IS_AZURE:
    BundleStorage = StorageClass(account_name=BUNDLE_AZURE_ACCOUNT_NAME,
                                 account_key=BUNDLE_AZURE_ACCOUNT_KEY,
                                 azure_container=BUNDLE_AZURE_CONTAINER)

    PublicStorage = StorageClass(account_name=AZURE_ACCOUNT_NAME,
                                 account_key=AZURE_ACCOUNT_KEY,
                                 azure_container=AZURE_CONTAINER)
else:
    BundleStorage = StorageClass()
    PublicStorage = StorageClass()

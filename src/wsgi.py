import os

from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise

settings_module = os.environ.setdefault('DJANGO_SETTINGS_MODULE', "settings.base")

application = DjangoWhiteNoise(get_wsgi_application())

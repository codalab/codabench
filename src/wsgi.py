import os

from django.core.wsgi import get_wsgi_application

settings_module = os.environ.setdefault('DJANGO_SETTINGS_MODULE', "settings.develop")

application = get_wsgi_application()

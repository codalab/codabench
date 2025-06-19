import os
import django

# For some reason this usually need to be between lines 2 and 3 to work properly
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

import routing  # or wherever your websocket_urlpatterns are

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.develop")
django.setup()


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})

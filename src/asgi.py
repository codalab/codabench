import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.develop")
django.setup()

# Django components must be imported after django.setup() - ignore flake8 import order
from channels.routing import ProtocolTypeRouter, URLRouter   # noqa: E402
from channels.auth import AuthMiddlewareStack   # noqa: E402
from django.core.asgi import get_asgi_application   # noqa: E402

import routing  # noqa: E402


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})

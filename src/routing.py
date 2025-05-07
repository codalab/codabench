# from channels.auth import AuthMiddlewareStack
# from django.urls import path
# from channels.routing import ProtocolTypeRouter, URLRouter

# from competitions import consumers


# application = ProtocolTypeRouter({
#     # (http->django views is added by default)

#     "websocket": AuthMiddlewareStack(URLRouter([
#         path("submission_input/<int:user_pk>/<int:submission_id>/<str:secret>/", consumers.SubmissionIOConsumer),
#         path("submission_output/", consumers.SubmissionOutputConsumer),
#         # path(r".*", consumers.SubmissionOutputConsumer),
#     ])),
# })



# apps/routing.py
from django.urls import re_path
from apps.competitions.consumers import SubmissionIOConsumer, SubmissionOutputConsumer

websocket_urlpatterns = [
    re_path(r'submission_input/(?P<user_pk>\d+)/(?P<submission_id>\d+)/(?P<secret>[^/]+)/$', SubmissionIOConsumer.as_asgi()),
    re_path(r'submission_output/$', SubmissionOutputConsumer.as_asgi()),
]

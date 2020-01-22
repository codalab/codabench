from channels.auth import AuthMiddlewareStack
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from competitions import consumers


application = ProtocolTypeRouter({
    # (http->django views is added by default)

    "websocket": AuthMiddlewareStack(URLRouter([
        path("submission_input/<int:submission_id>/", consumers.SubmissionIOConsumer),
        path("submission_output/", consumers.SubmissionOutputConsumer),
        # path(r".*", consumers.SubmissionOutputConsumer),
    ])),
})

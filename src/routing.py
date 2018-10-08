from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter

from competitions.consumers import SubmissionOutputConsumer


application = ProtocolTypeRouter({
    # (http->django views is added by default)

    "websocket": URLRouter([
        url(r"^submission_output/$", SubmissionOutputConsumer),
    ]),
})

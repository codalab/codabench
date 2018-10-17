from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter

from competitions import consumers


application = ProtocolTypeRouter({
    # (http->django views is added by default)

    "websocket": URLRouter([
        url(r"^submission_input/$", consumers.SubmissionInputConsumer),
        url(r"^submission_output/$", consumers.SubmissionOutputConsumer),
    ]),
})

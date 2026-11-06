import socket
import unittest

from django.conf import settings


def rabbitmq_is_reachable():
    """Whether the RabbitMQ management API answers, as it does in the docker setup."""
    try:
        socket.create_connection((settings.RABBITMQ_HOST, int(settings.RABBITMQ_MANAGEMENT_PORT)), timeout=1).close()
        reachable = True
    except OSError:
        reachable = False
    return reachable


# Skips tests that create or delete real RabbitMQ vhosts when no broker runs
requires_rabbitmq = unittest.skipUnless(rabbitmq_is_reachable(), "RabbitMQ is not reachable")

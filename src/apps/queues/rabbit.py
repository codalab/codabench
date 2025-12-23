import uuid

from django.conf import settings
from pyrabbit2.api import Client
from pyrabbit2.http import HTTPError, NetworkError

import logging
logger = logging.getLogger(__name__)


def _get_rabbit_connection():
    """Helper giving us a rabbit connection from settings.BROKER_URL"""
    if settings.RABBITMQ_PYRABBIT_URL:
        rabbit_api_url = settings.RABBITMQ_PYRABBIT_URL
    else:
        rabbit_api_url = f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/"
    return Client(
        rabbit_api_url,
        settings.RABBITMQ_DEFAULT_USER,
        settings.RABBITMQ_DEFAULT_PASS,
        scheme=settings.RABBITMQ_SCHEME
    )


def check_user_needs_initialization(user, connection):
    try:
        connection.get_user_permissions(user.rabbitmq_username)
        # We found the user, no need to initialize
        return False
    except (HTTPError, NetworkError):
        # User not found, needs initialization
        return True


def initialize_user(user, connection):
    """Check whether user has a rabbitmq account already, creates it if not."""
    logger.info(f"Making new rabbitmq user for {user}")

    # Only create a username/pass if none are set
    if not user.rabbitmq_username:
        user.rabbitmq_username = str(uuid.uuid4())
        user.rabbitmq_password = str(uuid.uuid4())

    connection.create_user(str(user.rabbitmq_username), str(user.rabbitmq_password))

    # Give user permissions to send submission updates
    connection.set_vhost_permissions(
        '/',
        str(user.rabbitmq_username),
        '.*',
        '.*submission-updates.*',
        '.*submission-updates.*'
    )

    # Was successful, save now
    user.save()


def create_queue(user, vhost=None):
    """Create a new queue with a random name and give full permissions to the owner AND our base account"""
    conn = _get_rabbit_connection()
    if check_user_needs_initialization(user, conn):
        initialize_user(user, conn)

    if not vhost:
        vhost = str(uuid.uuid4())
    conn.create_vhost(vhost)

    # Set permissions for our end user
    conn.set_vhost_permissions(
        vhost,
        user.rabbitmq_username,
        '.*',
        '.*',
        '.*'
    )

    # Set permissions for ourselves
    conn.set_vhost_permissions(
        vhost,
        settings.RABBITMQ_DEFAULT_USER,
        '.*',
        '.*',
        '.*'
    )

    return vhost


def delete_vhost(vhost):
    conn = _get_rabbit_connection()
    conn.delete_vhost(vhost)

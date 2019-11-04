import logging
import uuid

from django.conf import settings
from pyrabbit.api import Client
from pyrabbit.http import HTTPError, NetworkError

logger = logging.getLogger()


def _get_rabbit_connection():
    """Helper giving us a rabbit connection from settings.BROKER_URL"""
    host_with_port = f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/"
    return Client(host_with_port, settings.RABBITMQ_DEFAULT_USER, settings.RABBITMQ_DEFAULT_PASS)


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


def create_queue(user):
    """Create a new queue with a random name and give full permissions to the owner AND our base account"""
    conn = _get_rabbit_connection()
    if check_user_needs_initialization(user, conn):
        initialize_user(user, conn)

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

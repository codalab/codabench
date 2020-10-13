from urllib.parse import urlsplit

from .production import *

# Example structure:
#   amqps://username:password@toad.rmq.cloudamqp.com/vhost
CLOUDAMQP_URL = os.environ.get("CLOUDAMQP_URL")

BROKER_URL = CLOUDAMQP_URL
CELERY_BROKER_URL = CLOUDAMQP_URL

rabbit_url_pieces = urlsplit(CLOUDAMQP_URL)

RABBITMQ_DEFAULT_USER = os.environ.get('RABBITMQ_DEFAULT_USER', rabbit_url_pieces.username)
RABBITMQ_DEFAULT_PASS = os.environ.get('RABBITMQ_DEFAULT_PASS', rabbit_url_pieces.password)
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', rabbit_url_pieces.hostname)
# RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
RABBITMQ_MANAGEMENT_PORT = os.environ.get('RABBITMQ_MANAGEMENT_PORT', '15672')

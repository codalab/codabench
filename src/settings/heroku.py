from urllib.parse import urlsplit

from .production import *  # noqa: F401,F403

# Example structure:
#   amqps://username:password@toad.rmq.cloudamqp.com/vhost
# CLOUDAMQP_URL = os.environ.get("CLOUDAMQP_URL")

BROKER_URL = os.environ.get("BROKER_URL")
CELERY_BROKER_URL = BROKER_URL

rabbit_url_pieces = urlsplit(BROKER_URL)

# Different defaults from base settings
RABBITMQ_DEFAULT_USER = os.environ.get('RABBITMQ_DEFAULT_USER', rabbit_url_pieces.username)
RABBITMQ_DEFAULT_PASS = os.environ.get('RABBITMQ_DEFAULT_PASS', rabbit_url_pieces.password)
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', rabbit_url_pieces.hostname)
# RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
# RABBITMQ_SCHEME = os.environ.get('RABBITMQ_SCHEME', 'http')
# RABBITMQ_PYRABBIT_URL = os.environ.get('RABBITMQ_PYRABBIT_URL', rabbit_url_pieces.netloc.split('@')[-1])
RABBITMQ_MANAGEMENT_PORT = os.environ.get('RABBITMQ_MANAGEMENT_PORT', '15672')

# Force domain redirect
ENFORCE_HOST = os.environ.get('ENFORCE_HOST')
if ENFORCE_HOST:
    MIDDLEWARE = ('enforce_host.EnforceHostMiddleware',) + MIDDLEWARE

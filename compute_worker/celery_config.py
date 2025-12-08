import os
import ssl

broker_url = os.environ.get('BROKER_URL')
if os.environ.get('BROKER_USE_SSL', False):
    broker_use_ssl = {
        "cert_reqs": ssl.CERT_NONE,
    }
worker_concurrency = 1
worker_prefetch_multiplier = 1
task_acks_late = True

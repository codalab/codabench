import os


broker_url = os.environ.get('BROKER_URL')
broker_use_ssl = os.environ.get('BROKER_USE_SSL', False)
worker_concurrency = 1
worker_prefetch_multiplier = 1
task_acks_late = True

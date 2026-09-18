import os
import ssl
import time


broker_url = os.environ.get('BROKER_URL')
if os.environ.get('BROKER_USE_SSL', False):
    broker_use_ssl = {
        "cert_reqs": ssl.CERT_NONE,
    }
worker_concurrency = 1
worker_prefetch_multiplier = 1
task_acks_late = True


def _read_worker_token(max_retries=10, delay=2):
    token_path = os.environ.get('WORKER_TOKEN_FILE', '/run/secrets/worker_token')
    for attempt in range(max_retries):
        if os.path.exists(token_path):
            with open(token_path) as f:
                return f.read().strip()
        time.sleep(delay)
    raise RuntimeError(f"Worker token introuvable dans {token_path} après {max_retries} tentatives.")


CODABENCH_API_TOKEN = _read_worker_token()


def get_auth_headers():
    return {'Authorization': f'Token {CODABENCH_API_TOKEN}'}

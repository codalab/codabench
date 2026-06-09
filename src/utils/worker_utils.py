import logging
import time

import requests
from django.conf import settings
from queues.models import Queue

logger = logging.getLogger(__name__)

PIDBOX_SUFFIX = ".celery.pidbox"


def _rabbitmq_auth():
    return (settings.RABBITMQ_DEFAULT_USER, settings.RABBITMQ_DEFAULT_PASS)


def _rabbitmq_base_url():
    return f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/api"


def _build_vhost_to_source_map():
    """{ vhost_string: queue_source_name }. Default vhost '/' → 'default'."""
    mapping = {"/": "default"}
    for q in Queue.objects.exclude(vhost__isnull=True).values("vhost", "name"):
        mapping[str(q["vhost"])] = q["name"]
    return mapping


def _fetch_all_queues():
    resp = requests.get(
        f"{_rabbitmq_base_url()}/queues",
        auth=_rabbitmq_auth(),
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def is_compute_worker(worker_name):
    return worker_name.startswith("compute-worker")


def fetch_compute_workers():
    try:
        all_queues = _fetch_all_queues()
    except Exception:
        logger.exception("Failed to fetch queues from RabbitMQ Management API")
        return [], [], []

    try:
        vhost_to_source = _build_vhost_to_source_map()
    except Exception:
        logger.exception("Failed to build vhost→source map")
        return [], [], []

    by_vhost = {}
    for q in all_queues:
        by_vhost.setdefault(q["vhost"], []).append(q)

    workers = []
    private_workers = []
    queue_stats = []
    now = time.time()

    for vhost, queues in by_vhost.items():
        source_name = vhost_to_source.get(vhost)
        if not source_name:
            continue

        # Queue de travail Celery
        cw_queue = next(
            (q for q in queues if q["name"] == "compute-worker"),
            None,
        )

        jobs_pending = cw_queue.get("messages_ready", 0) if cw_queue else 0
        jobs_running = (
            cw_queue.get("messages_unacknowledged", 0)
            if cw_queue
            else 0
        )
        workers_count = cw_queue.get("consumers", 0) if cw_queue else 0

        queue_stats.append(
            {
                "source_name": source_name,
                "jobs_pending": jobs_pending,
                "jobs_running": jobs_running,
                "workers_count": workers_count,
            }
        )

        # Workers individuels détectés via pidbox
        for q in queues:
            name = q["name"]

            if not (
                name.startswith("compute-worker@")
                and name.endswith(PIDBOX_SUFFIX)
            ):
                continue

            hostname = name[: -len(PIDBOX_SUFFIX)]

            if not is_compute_worker(hostname):
                continue

            online = q.get("consumers", 0) > 0

            worker = {
                "hostname": hostname,
                "status": "available" if online else "unavailable",
                "last_seen": now,
                "queue_source": source_name,
                "queue_names": ["compute-worker"],
            }

            if source_name == "default":
                workers.append(worker)
            else:
                private_workers.append(worker)

    workers.sort(key=lambda w: w["hostname"])
    private_workers.sort(
        key=lambda w: (w["queue_source"], w["hostname"])
    )
    queue_stats.sort(key=lambda q: q["source_name"])

    return workers, private_workers, queue_stats

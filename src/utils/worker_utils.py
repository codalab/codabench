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
        return [], []

    try:
        vhost_to_source = _build_vhost_to_source_map()
    except Exception:
        logger.exception("Failed to build vhost→source map")
        return [], []

    by_vhost: dict[str, list] = {}
    for q in all_queues:
        by_vhost.setdefault(q["vhost"], []).append(q)

    workers = []
    private_workers = []
    now = time.time()

    for vhost, queues in by_vhost.items():
        source_name = vhost_to_source.get(vhost)
        if not source_name:
            continue

        cw_queue = next((q for q in queues if q["name"] == "compute-worker"), None)
        messages_unacked = cw_queue.get("messages_unacknowledged", 0) if cw_queue else 0
        cw_consumers = cw_queue.get("consumers", 0) if cw_queue else 0

        vhost_workers = []
        for pidbox_q in queues:
            name = pidbox_q["name"]
            if not (
                name.endswith(PIDBOX_SUFFIX) and name.startswith("compute-worker@")
            ):
                continue
            hostname = name[: -len(PIDBOX_SUFFIX)]
            if not is_compute_worker(hostname):
                continue
            vhost_workers.append(
                {
                    "hostname": hostname,
                    "pidbox_alive": pidbox_q.get("consumers", 0) > 0,
                }
            )

        jobs_to_distribute = messages_unacked

        for w in vhost_workers:
            if not w["pidbox_alive"] or cw_consumers == 0:
                status = "unavailable"
                running_jobs = 0
            elif jobs_to_distribute > 0:
                status = "busy"
                running_jobs = 1
                jobs_to_distribute -= 1
            else:
                status = "available"
                running_jobs = 0

            worker = {
                "hostname": w["hostname"],
                "status": status,
                "running_jobs": running_jobs,
                "last_seen": now,
                "queue_source": source_name,
                "queue_names": ["compute-worker"],
            }

            if source_name == "default":
                workers.append(worker)
            else:
                private_workers.append(worker)

    workers.sort(key=lambda x: x["hostname"])
    private_workers.sort(key=lambda x: (x["queue_source"], x["hostname"]))
    return workers, private_workers

from queues.models import Queue

import logging
import time
import requests
from django.conf import settings

from queues.models import Queue as QueueModel

logger = logging.getLogger(__name__)

PIDBOX_SUFFIX = ".celery.pidbox"
WORKERS_REGISTRY_KEY = "workers:registry"
WORKER_HEARTBEAT_TTL = 180


def extract_queue_names(active_queues):
    names = set()
    for q in active_queues or []:
        if isinstance(q, dict) and q.get("name"):
            names.add(q["name"])
    return names


def known_compute_queue_names():
    return set(
        Queue.objects.exclude(name__isnull=True)
        .exclude(name="")
        .values_list("name", flat=True)
    )


def is_compute_worker(worker_name, queue_names, known_queue_names):
    return (
        bool(queue_names & known_queue_names)
        or "compute-worker" in queue_names
        or worker_name.startswith("compute-worker")
    )

def _get_rabbitmq_auth():
    return (
        settings.RABBITMQ_DEFAULT_USER,
        settings.RABBITMQ_DEFAULT_PASS,
    )


def _get_rabbitmq_base_url():
    return (
        f"http://{settings.RABBITMQ_HOST}"
        f":{settings.RABBITMQ_MANAGEMENT_PORT}/api"
    )


def _build_vhost_to_source_map():
    mapping = {"/": "default"}
    for q in QueueModel.objects.exclude(vhost__isnull=True).values("vhost", "name"):
        mapping[str(q["vhost"])] = q["name"]
    return mapping

def _fetch_all_queues():
    resp = requests.get(
        f"{_get_rabbitmq_base_url()}/queues",
        auth=_get_rabbitmq_auth(),
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_compute_workers():
    try:
        all_queues = _fetch_all_queues()
    except Exception:
        logger.exception("Failed to fetch queues from RabbitMQ Management API")
        return [], []

    vhost_to_source = _build_vhost_to_source_map()

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

        pidbox_queues = [
            q for q in queues
            if q["name"].endswith(PIDBOX_SUFFIX)
            and q["name"].startswith("compute-worker@")
        ]

        for pidbox_q in pidbox_queues:
            hostname = pidbox_q["name"][: -len(PIDBOX_SUFFIX)]

            if not is_compute_worker(hostname, {"compute-worker"}, set()):
                continue

            pidbox_alive = pidbox_q.get("consumers", 0) > 0

            if not pidbox_alive or cw_consumers == 0:
                status = "unavailable"
                running_jobs = 0
            elif messages_unacked > 0:
                status = "busy"
                running_jobs = messages_unacked
            else:
                status = "available"
                running_jobs = 0

            worker = {
                "hostname": hostname,
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
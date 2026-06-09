import logging
import time
from collections import defaultdict

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


def _fetch_all_channels():
    resp = requests.get(
        f"{_rabbitmq_base_url()}/channels",
        auth=_rabbitmq_auth(),
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def _fetch_all_consumers():
    resp = requests.get(
        f"{_rabbitmq_base_url()}/consumers",
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
        all_channels = _fetch_all_channels()
        all_consumers = _fetch_all_consumers()
    except Exception:
        logger.exception("Failed to fetch RabbitMQ data")
        return [], [], []

    try:
        vhost_to_source = _build_vhost_to_source_map()
    except Exception:
        logger.exception("Failed to build vhost→source map")
        return [], [], []

    connection_to_unacked = defaultdict(int)
    for ch in all_channels:
        connection_name = (ch.get("connection_details") or {}).get("name")
        if not connection_name:
            continue
        unacked = int(ch.get("messages_unacknowledged", 0) or 0)
        if unacked > connection_to_unacked[connection_name]:
            connection_to_unacked[connection_name] = unacked

    worker_to_pidbox_connections = defaultdict(list)
    for c in all_consumers:
        q = c.get("queue") or {}
        qname = q.get("name") or ""
        if not (qname.startswith("compute-worker@") and qname.endswith(PIDBOX_SUFFIX)):
            continue

        hostname = qname[: -len(PIDBOX_SUFFIX)]
        if not is_compute_worker(hostname):
            continue

        channel_details = c.get("channel_details") or {}
        connection_name = channel_details.get("connection_name") or channel_details.get("name")
        if not connection_name:
            continue

        vhost = q.get("vhost") or "/"
        worker_to_pidbox_connections[(vhost, hostname)].append(
            {
                "connection_name": connection_name,
                "active": bool(c.get("active", True)),
            }
        )

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

        cw_queue = next((q for q in queues if q["name"] == "compute-worker"), None)
        messages_ready = cw_queue.get("messages_ready", 0) if cw_queue else 0
        messages_unacked = cw_queue.get("messages_unacknowledged", 0) if cw_queue else 0
        cw_consumers = cw_queue.get("consumers", 0) if cw_queue else 0

        queue_stats.append(
            {
                "source_name": source_name,
                "jobs_pending": messages_ready,
                "jobs_running": messages_unacked,
                "workers_count": cw_consumers,
            }
        )

        for pidbox_q in queues:
            name = pidbox_q.get("name") or ""
            if not (name.startswith("compute-worker@") and name.endswith(PIDBOX_SUFFIX)):
                continue

            hostname = name[: -len(PIDBOX_SUFFIX)]
            if not is_compute_worker(hostname):
                continue

            pidbox_links = worker_to_pidbox_connections.get((vhost, hostname), [])
            online = any(link.get("active") for link in pidbox_links)
            busy = any(
                connection_to_unacked.get(link["connection_name"], 0) > 0
                for link in pidbox_links
            )

            if not online:
                status = "unavailable"
            elif busy:
                status = "busy"
            else:
                status = "available"

            worker = {
                "hostname": hostname,
                "status": status,
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
    queue_stats.sort(key=lambda x: x["source_name"])

    return workers, private_workers, queue_stats

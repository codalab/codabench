import asyncio
import logging
import time

from asgiref.sync import sync_to_async
from celery._state import app_or_default
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from queues.models import Queue

logger = logging.getLogger(__name__)


def _extract_queue_names(active_queues):
    names = set()
    for q in active_queues or []:
        if isinstance(q, dict) and q.get("name"):
            names.add(q["name"])
    return names


def _known_compute_queue_names():
    return set(
        Queue.objects.exclude(name__isnull=True)
        .exclude(name="")
        .values_list("name", flat=True)
    )


def _is_compute_worker(worker_name, queue_names, known_queue_names):
    return (
        bool(queue_names & known_queue_names)
        or "compute-worker" in queue_names
        or worker_name.startswith("compute-worker")
        or worker_name.startswith("CW")
    )


def _get_broker_host(broker_url):
    if not broker_url or "@" not in broker_url:
        return None
    try:
        return broker_url.split("@", 1)[1].split("/", 1)[0].split(":", 1)[0]
    except Exception:
        return None


def _resolve_broker_url(celery_app, broker_url):
    if not broker_url:
        return broker_url

    if "@localhost:" not in broker_url:
        return broker_url

    default_broker = getattr(celery_app.conf, "broker_url", None)
    default_host = _get_broker_host(default_broker)

    if not default_host or default_host == "localhost":
        return broker_url

    return broker_url.replace("@localhost:", f"@{default_host}:")


class ComputeWorkersConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if user is None or user.is_anonymous:
            await self.close()
            return

        await self.accept()
        self._running = True
        self._task = asyncio.create_task(self._push_workers_loop())

    async def disconnect(self, close_code):
        self._running = False

        task = getattr(self, "_task", None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except RuntimeError:
                pass

    async def _push_workers_loop(self):
        try:
            while self._running:
                workers = await sync_to_async(self._load_snapshot, thread_sensitive=True)()

                if not self._running:
                    break

                try:
                    await self.send_json(
                        {
                            "type": "workers.snapshot",
                            "workers": workers,
                        }
                    )
                except RuntimeError:
                    break

                await asyncio.sleep(3)

        except asyncio.CancelledError:
            pass

    def _load_snapshot(self):
        celery_app = app_or_default()
        known_queue_names = _known_compute_queue_names()

        workers = []
        seen = set()
        inspected_brokers = set()

        broker_sources = []

        default_broker = getattr(celery_app.conf, "broker_url", None)
        if default_broker:
            broker_sources.append(("default", default_broker))

        private_queues = (
            Queue.objects.filter(competitions__isnull=False)
            .exclude(name__isnull=True)
            .exclude(name="")
            .distinct()
        )

        for queue in private_queues:
            broker_url = _resolve_broker_url(celery_app, queue.broker_url)
            if broker_url:
                broker_sources.append((queue.name, broker_url))

        for source_name, broker_url in broker_sources:
            if broker_url in inspected_brokers:
                continue
            inspected_brokers.add(broker_url)

            try:
                broker_app = celery_app.__class__(
                    "compute-worker-monitor",
                    broker=broker_url,
                )

                inspector = broker_app.control.inspect(timeout=2)

                if inspector is None:
                    continue

                stats = inspector.stats() or {}
                active = inspector.active() or {}
                reserved = inspector.reserved() or {}
                active_queues = inspector.active_queues() or {}

            except Exception:
                logger.exception(
                    "Unable to inspect Celery workers for broker %s",
                    source_name,
                )
                continue

            for worker_name in stats.keys():
                queues = active_queues.get(worker_name, []) or []
                queue_names = _extract_queue_names(queues)

                if not _is_compute_worker(worker_name, queue_names, known_queue_names):
                    continue

                unique_key = (source_name, worker_name)
                if unique_key in seen:
                    continue
                seen.add(unique_key)

                running_jobs = len(active.get(worker_name, [])) + len(reserved.get(worker_name, []))
                status = "busy" if running_jobs > 0 else "available"

                workers.append(
                    {
                        "hostname": worker_name,
                        "status": status,
                        "running_jobs": running_jobs,
                        "timestamp": time.time(),
                        "queue_source": source_name,
                        "queue_names": sorted(queue_names),
                    }
                )

        workers.sort(key=lambda x: (x.get("queue_source", ""), x.get("hostname", "")))
        return workers

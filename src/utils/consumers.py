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

    async def _push_workers_loop(self):
        while self._running:
            workers = await sync_to_async(self._load_snapshot)()
            await self.send_json(
                {
                    "type": "workers.snapshot",
                    "workers": workers,
                }
            )
            await asyncio.sleep(3)

    def _load_snapshot(self):
        celery_app = app_or_default()
        inspector = celery_app.control.inspect(timeout=2)

        if inspector is None:
            return []

        try:
            stats = inspector.stats() or {}
            active = inspector.active() or {}
            reserved = inspector.reserved() or {}
            active_queues = inspector.active_queues() or {}
        except Exception:
            logger.exception("Unable to inspect Celery workers")
            return []

        known_queue_names = _known_compute_queue_names()
        workers = []

        for worker_name in stats.keys():
            queues = active_queues.get(worker_name, []) or []
            queue_names = _extract_queue_names(queues)

            if not _is_compute_worker(worker_name, queue_names, known_queue_names):
                continue

            running_jobs = len(active.get(worker_name, [])) + len(reserved.get(worker_name, []))
            status = "busy" if running_jobs > 0 else "available"

            workers.append(
                {
                    "hostname": worker_name,
                    "status": status,
                    "running_jobs": running_jobs,
                    "timestamp": time.time(),
                    "queue_names": sorted(queue_names),
                }
            )

        return workers

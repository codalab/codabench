import asyncio
import json
import logging
import time

from competitions.models import Competition

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django_redis import get_redis_connection

from utils.worker_utils import WORKER_HEARTBEAT_TTL, WORKERS_REGISTRY_KEY

logger = logging.getLogger(__name__)

r = get_redis_connection("default")


def _load_snapshot(competition_queue_name=None):
    raw = r.hgetall(WORKERS_REGISTRY_KEY)
    workers = []
    private_workers = []
    now = time.time()

    for _, value in raw.items():
        try:
            worker = json.loads(value)
        except Exception:
            continue

        if now - worker.get("last_seen", 0) > WORKER_HEARTBEAT_TTL:
            continue

        if worker.get("queue_source") == "default":
            workers.append(worker)
        else:
            # Worker privé : n'afficher que si la queue correspond à la compétition
            if competition_queue_name and worker.get("queue_source") == competition_queue_name:
                private_workers.append(worker)

    workers.sort(key=lambda x: x.get("hostname", ""))
    private_workers.sort(key=lambda x: (x.get("queue_source", ""), x.get("hostname", "")))
    return workers, private_workers


def _get_competition_queue_name(competition_id):
    if not competition_id:
        return None
    try:
        competition = Competition.objects.select_related("queue").get(pk=competition_id)
        if competition.queue and competition.queue.name:
            return competition.queue.name
    except Exception:
        logger.warning("Competition %s not found or has no queue", competition_id)
    return None

import logging

logger = logging.getLogger(__name__)


class ComputeWorkersConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

    async def connect(self):
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            await self.close()
            return

        await self.accept()
        await self.channel_layer.group_add("compute_workers", self.channel_name)
        self._competition_queue_name = None
        self._running = True
        self._subscribed = asyncio.Event()
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
        try:
            stats = inspector.stats() or {}
            active = inspector.active() or {}
            reserved = inspector.reserved() or {}
            active_queues = inspector.active_queues() or {}
        except Exception:
            logger.exception("Unable to inspect Celery workers")
            return []

            while self._running:
                workers, private_workers = await sync_to_async(_load_snapshot)(
                    self._competition_queue_name
                )
                if not self._running:
                    break
                try:
                    await self.send_json({
                        "type": "workers.snapshot",
                        "workers": workers,
                        "private_workers": private_workers,
                    })
                except RuntimeError:
                    break
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            pass

        for worker_name in stats.keys():
            queues = active_queues.get(worker_name, []) or []
            queue_names = []

            for q in queues:
                if isinstance(q, dict) and q.get("name"):
                    queue_names.append(q["name"])

            is_compute_worker = (
                "compute-worker" in queue_names
                or worker_name.startswith("compute-worker")
                or worker_name.startswith("CW")
            )

            if not is_compute_worker:
                continue

            running_jobs = (
                len(active.get(worker_name, []))
                + len(reserved.get(worker_name, []))
            )
            status = "busy" if running_jobs > 0 else "available"

            workers.append(
                {
                    "hostname": worker_name,
                    "status": status,
                    "running_jobs": running_jobs,
                    "timestamp": time.time(),
                }
            )

        return workers

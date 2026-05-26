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
    """
    Charge les workers depuis Redis.
    - workers par défaut : toujours inclus (queue_source == 'default')
    - workers privés : inclus uniquement si leur queue_source correspond
      à la queue de la compétition courante
    """
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
    """Retourne le nom de la queue de la compétition, ou None."""
    if not competition_id:
        return None
    try:
        competition = Competition.objects.select_related("queue").get(pk=competition_id)
        if competition.queue and competition.queue.name:
            return competition.queue.name
    except Exception:
        logger.warning("Competition %s not found or has no queue", competition_id)
    return None


class ComputeWorkersConsumer(AsyncJsonWebsocketConsumer):

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
        await self.channel_layer.group_discard("compute_workers", self.channel_name)
        task = getattr(self, "_task", None)
        if task:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, RuntimeError):
                pass

    async def receive_json(self, content):
        logger.debug("WebSocket received: %s", content)
        if content.get("type") == "subscribe":
            competition_id = content.get("competition_id")
            self._competition_queue_name = await sync_to_async(_get_competition_queue_name)(
                competition_id)
            self._subscribed.set()

    async def _push_workers_loop(self):
        try:
            try:
                await asyncio.wait_for(self._subscribed.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("WebSocket subscribe timeout, proceeding without competition filter")

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

    async def worker_health(self, event):
        worker = event["worker"]
        is_default = worker.get("queue_source") == "default"
        is_mine = (
            self._competition_queue_name is not None
            and worker.get("queue_source") == self._competition_queue_name
        )
        if not is_default and not is_mine:
            return
        try:
            workers, private_workers = await sync_to_async(_load_snapshot)(
                self._competition_queue_name
            )
            await self.send_json({
                "type": "workers.snapshot",
                "workers": workers,
                "private_workers": private_workers,
            })
        except RuntimeError:
            pass

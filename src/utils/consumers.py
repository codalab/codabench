# utils/consumers.py

import asyncio
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from utils.worker_utils import fetch_compute_workers


logger = logging.getLogger(__name__)


def _get_competition_queue_name(competition_id):
    if not competition_id:
        return None
    try:
        from competitions.models import Competition
        competition = Competition.objects.select_related("queue").get(pk=competition_id)
        if competition.queue and competition.queue.name:
            return competition.queue.name
    except Exception:
        logger.warning("Competition %s not found or has no queue", competition_id)
    return None


def _load_snapshot(competition_queue_name=None):
    workers, private_workers = fetch_compute_workers()

    if competition_queue_name:
        private_workers = [
            w for w in private_workers
            if w.get("queue_source") == competition_queue_name
        ]
    else:
        private_workers = []

    return workers, private_workers


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
        if content.get("type") == "subscribe":
            competition_id = content.get("competition_id")
            self._competition_queue_name = await sync_to_async(
                _get_competition_queue_name
            )(competition_id)
            self._subscribed.set()

    async def _push_workers_loop(self):
        try:
            try:
                await asyncio.wait_for(self._subscribed.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(
                    "WebSocket subscribe timeout, proceeding without competition filter"
                )

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

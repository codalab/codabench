import asyncio
import json
import logging
import time

from django_redis import get_redis_connection

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)

WORKERS_REGISTRY_KEY = "workers:registry"
WORKER_HEARTBEAT_TTL = 35

r = get_redis_connection("default")


def _load_snapshot():
    raw = r.hgetall(WORKERS_REGISTRY_KEY)
    workers = []
    now = time.time()
    for _, value in raw.items():
        try:
            worker = json.loads(value)
        except Exception:
            continue
        last_seen = worker.get("last_seen", 0)
        if now - last_seen > WORKER_HEARTBEAT_TTL:
            continue
        workers.append(worker)
    workers.sort(key=lambda x: (x.get("queue_source", ""), x.get("hostname", "")))
    return workers


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
            except (asyncio.CancelledError, RuntimeError):
                pass

    async def _push_workers_loop(self):
        try:
            while self._running:
                workers = await sync_to_async(_load_snapshot)()
                if not self._running:
                    break
                try:
                    await self.send_json({
                        "type": "workers.snapshot",
                        "workers": workers,
                    })
                except RuntimeError:
                    break
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            pass

    async def worker_health(self, event):
        try:
            await self.send_json({
                "type": "workers.snapshot",
                "workers": [event["worker"]],
            })
        except RuntimeError:
            pass

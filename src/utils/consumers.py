import asyncio
import time

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from celery._state import app_or_default


class ComputeWorkersConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self._running = True
        self._task = asyncio.create_task(self._push_workers_loop())

    async def disconnect(self, close_code):
        self._running = False
        if hasattr(self, "_task"):
            self._task.cancel()

    async def _push_workers_loop(self):
        while self._running:
            workers = await sync_to_async(self._load_snapshot)()
            await self.send_json({
                "type": "workers.snapshot",
                "workers": workers,
            })
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
            return []

        workers = []

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

            running_jobs = len(active.get(worker_name, [])) + len(reserved.get(worker_name, []))
            status = "busy" if running_jobs > 0 else "available"

            workers.append({
                "hostname": worker_name,
                "status": status,
                "running_jobs": running_jobs,
                "timestamp": time.time(),
            })

        return workers
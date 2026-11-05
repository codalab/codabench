"""Run shared container API checks against Docker, Podman, or Apptainer."""

import os
from pathlib import Path
import sys
import unittest
import uuid

import docker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apptainer_backend import APIClient


class ContainerEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = os.environ["CONTAINER_ENGINE_EXECUTABLE"]
        cls.image = os.environ.get("TEST_IMAGE", "codabench-compute-worker:ci")
        if cls.engine == "apptainer":
            cls.client = APIClient()
            cls.client.images = {
                cls.image: str(Path(os.environ["TEST_SIF"]).resolve())
            }
        elif cls.engine in ("docker", "podman"):
            cls.client = docker.APIClient(
                base_url=os.environ["CONTAINER_SOCKET"], version="auto", timeout=30
            )
        else:
            raise ValueError(f"Unsupported container engine: {cls.engine}")

    @classmethod
    def tearDownClass(cls):
        if cls.engine != "apptainer":
            cls.client.close()

    def create_container(self, code):
        container = self.client.create_container(
            self.image,
            name=f"worker-test-{uuid.uuid4().hex}",
            host_config=self.client.create_host_config(binds={}, auto_remove=False),
            command=["/.venv/bin/python", "-c", code],
            entrypoint=[],
            working_dir="/tmp",
            environment=["WORKER_TEST_VALUE=configured", "PYTHONUNBUFFERED=1"],
        )
        self.addCleanup(self.client.remove_container, container, v=True, force=True)
        return container

    # 1. Check the image loaded by the runtime job.
    def test_01_inspect_image(self):
        self.assertTrue(self.client.inspect_image(self.image)["Id"])

    # 2. Check the worker environment, output streams, and exit status.
    def test_02_execution(self):
        container = self.create_container(
            "import os, sys, time; "
            "import celery, docker, requests, websockets; "
            "assert os.getcwd() == '/tmp'; "
            "assert os.environ['WORKER_TEST_VALUE'] == 'configured'; "
            "print('worker stdout'); "
            "print('worker stderr', file=sys.stderr); "
            "time.sleep(1); sys.exit(23)"
        )
        self.client.start(container)
        chunks = list(self.client.attach(
            container, demux=True, stream=True, logs=True
        ))
        self.assertEqual(
            b"".join(chunk[0] or b"" for chunk in chunks), b"worker stdout\n"
        )
        self.assertEqual(
            b"".join(chunk[1] or b"" for chunk in chunks), b"worker stderr\n"
        )
        self.assertEqual(self.client.wait(container)["StatusCode"], 23)
        self.assertNotEqual(
            self.client.inspect_container(container)["State"]["Status"].lower(),
            "running",
        )

    # 3. Check explicit termination and the resulting exit status.
    def test_03_kill(self):
        container = self.create_container("import time; time.sleep(300)")
        self.client.start(container)
        self.assertEqual(
            self.client.inspect_container(container)["State"]["Status"].lower(),
            "running",
        )
        self.client.kill(container)
        self.assertEqual(self.client.wait(container)["StatusCode"], 137)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""The Docker API subset used by the pinned Codabench worker; no daemon."""
import codecs
import json
import os
from pathlib import Path
import selectors
import shlex
import signal
import subprocess
import tempfile
import uuid


class APIClient:
    def __init__(self):
        # Only pre-staged competition images are permitted on this shared queue.
        self.images = json.loads(os.environ.get("APPTAINER_IMAGE_MAP", "{}"))
        self.containers = {}

    def inspect_image(self, image):
        path = self.images.get(image.removeprefix("docker://"))
        if not path or not Path(path).is_file():
            raise FileNotFoundError(f"Image not staged for Juliet: {image}")
        return {"Id": path}

    def pull(self, image, **kwargs):
        self.inspect_image(image)
        yield {"status": "Status: Image is up to date (staged SIF)"}

    def create_host_config(self, **kwargs):
        return kwargs

    def create_container(self, image, *, name, host_config, command,
                         working_dir, environment, network_disabled=False, **kwargs):
        """Prepare an Apptainer command and return its Docker-compatible ID.

        Register the command without starting it. The image must already be
        mapped to a local SIF. Bind sources stay inside /codabench; evaluation
        scratch directories and the execution environment are private.
        """
        # Resolve the pre-staged image and reject a duplicate active name.
        sif = self.inspect_image(image)["Id"]
        if name in self.containers:
            raise RuntimeError(f"Container already exists: {name}")
        # Retain the TemporaryDirectory object until remove_container cleans it.
        scratch = tempfile.TemporaryDirectory(prefix="evaluation-")
        root = Path(scratch.name)
        # Execute the program in the SIF, rather than its image runscript.
        args = [
            "/usr/bin/apptainer", "exec",
            "--userns",              # Use an unprivileged user namespace.
            "--containall",          # Isolate filesystems, PID, IPC and environment.
            "--cleanenv",            # Exclude ordinary inherited environment values.
            "--no-eval",             # Disable shell evaluation of environment/OCI args.
            "--no-privs",            # Drop root privileges inside the container.
            "--writable-tmpfs",      # Add a temporary overlay; leave the SIF unchanged.
            "--no-mount", "hostfs,cwd,bind-paths",  # Disable automatic host/admin binds.
            "--pwd", working_dir,    # Set the program's working directory.
        ]
        # Give this evaluation its own writable home and temporary files.
        # Let --containall supply container-local /dev/shm: binding a scratch
        # directory there can leave it mounted and make cleanup fail with EBUSY.
        for part in ("home", "tmp"):
            (root / part).mkdir()
        args += ["--home", f"{root}/home:/home/competition",
                 "--bind", f"{root}/tmp:/tmp",
                 "--bind", f"{root}/tmp:/var/tmp"]
        # Translate Codabench volume mappings to src:destination:mode binds.
        for source, mount in host_config["binds"].items():
            # Resolve symlinks before checking the permitted source directory.
            resolved = Path(source).resolve()
            if not resolved.is_relative_to(Path("/codabench").resolve()):
                scratch.cleanup()
                raise ValueError(f"Bind source outside worker directory: {source}")
            destination = mount["bind"]
            # Commas/colons delimit Apptainer bind specifications, so reject them
            # in paths instead of allowing an additional mount to be parsed.
            if any(c in source + destination for c in ",:\n"):
                scratch.cleanup()
                raise ValueError("Unsupported character in bind path")
            # Docker's SELinux label option "z" has no effect here; only ro/rw
            # applies. Always force the shared corpus mount to read-only.
            mode = "ro" if "ro" in mount.get("mode", "").split(",") else "rw"
            if destination == "/app/data":
                mode = "ro"
            args += ["--bind", f"{source}:{destination}:{mode}"]
        # --nv supplies NVIDIA devices/libraries; the Slurm step's CUDA mask
        # and device cgroup restrict the GPU available to this evaluation.
        if host_config.get("device_requests"):
            if not os.environ.get("CUDA_VISIBLE_DEVICES"):
                scratch.cleanup()
                raise RuntimeError("Slurm did not set CUDA_VISIBLE_DEVICES")
            args += ["--nv"]
        # A separate network namespace with "none" removes external networking
        # when the upstream worker requests it; otherwise keep its network policy.
        if network_disabled:
            args += ["--net", "--network", "none"]
        # Match Docker's command splitting without adding a shell invocation.
        argv = shlex.split(command) if isinstance(command, str) else list(command)
        if not argv:
            scratch.cleanup()
            raise ValueError("Empty command")
        args += [sif, *argv]
        # Build a minimal environment for the nested Apptainer executable.
        # Outer binds, broker credentials and Apptainer overrides are excluded.
        env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp",
               "APPTAINER_TMPDIR": str(root / "tmp")}
        # APPTAINERENV_ explicitly injects the selected values into the payload
        # despite --cleanenv; values baked into the image remain available.
        values = dict(item.split("=", 1) for item in environment)
        # HOME is controlled by --home; Apptainer rejects APPTAINERENV_HOME.
        values.pop("HOME", None)
        values.update(BENCHOPT_CACHE="/tmp/benchopt")
        if host_config.get("device_requests"):
            values["CUDA_VISIBLE_DEVICES"] = os.environ["CUDA_VISIBLE_DEVICES"]
        for key, value in values.items():
            env["APPTAINERENV_" + key] = value
        # Store the prepared descriptor for start/attach/wait/remove; no process
        # exists until start is called.
        identifier = uuid.uuid4().hex
        self.containers[identifier] = {"name": name, "args": args, "env": env,
                                       "scratch": scratch, "process": None}
        return {"Id": identifier}

    def _get(self, container):
        key = container["Id"] if isinstance(container, dict) else container
        if key not in self.containers:
            key = next(k for k, v in self.containers.items() if v["name"] == key)
        return key, self.containers[key]

    def start(self, container):
        """Print the prepared command and start it in its own process group."""
        _, state = self._get(container)
        # Log argv with shell quoting for readability; execution still uses argv.
        print("Running command:", shlex.join(state["args"]), flush=True)
        # Separate the group for cleanup; capture each output stream independently.
        state["process"] = subprocess.Popen(
            state["args"], env=state["env"], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)

    def attach(self, container, **kwargs):
        """Yield demultiplexed UTF-8 stdout/stderr chunks until both pipes close.

        Each item is (stdout_bytes, None) or (None, stderr_bytes), as required
        by the pinned worker's streaming attach call. Drain buffered output
        even if the process has already exited. Incremental decoding preserves
        characters split across reads and replaces invalid UTF-8 input.
        Docker keyword arguments are accepted for call compatibility.
        """
        _, state = self._get(container)
        process = state["process"]
        # Keep a decoder per stream so a partial character is completed on the
        # next read before the upstream worker decodes the yielded bytes.
        decoders = [codecs.getincrementaldecoder("utf-8")(errors="replace") for _ in range(2)]
        with selectors.DefaultSelector() as selector:
            # Register non-blocking pipes: 0 identifies stdout, 1 stderr.
            for index, stream in enumerate((process.stdout, process.stderr)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, index)
            while selector.get_map():
                for key, _ in selector.select(timeout=1):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    payload = decoders[key.data].decode(chunk, final=not chunk).encode("utf-8")
                    # EOF flushes any decoder remainder and removes that pipe.
                    if not chunk:
                        selector.unregister(key.fileobj)
                    if payload:
                        yield (payload, None) if key.data == 0 else (None, payload)

    def inspect_container(self, container):
        _, state = self._get(container)
        process = state["process"]
        running = process is not None and process.poll() is None
        return {"State": {"Status": "running" if running else "exited"}}

    def wait(self, container, **kwargs):
        _, state = self._get(container)
        code = state["process"].wait()
        return {"StatusCode": code if code >= 0 else 128 - code}

    def kill(self, container, **kwargs):
        _, state = self._get(container)
        process = state["process"]
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def remove_container(self, container, force=False, **kwargs):
        try:
            key, state = self._get(container)
        except (StopIteration, KeyError):
            return
        if force:
            self.kill(container)
        process = state["process"]
        if process is not None:
            process.wait()
            process.stdout.close()
            process.stderr.close()
        state["scratch"].cleanup()
        del self.containers[key]


def self_check():
    """Check the adapter with local Python processes; do not invoke Apptainer."""
    import sys
    # 1. Register a placeholder SIF to exercise image lookup and descriptor creation.
    client = APIClient()
    with tempfile.TemporaryDirectory() as directory:
        image = Path(directory) / "image.sif"
        image.touch()
        client.images = {"test:1": str(image)}
        # 2. Prepare a descriptor and check that its environment excludes broker keys.
        container = client.create_container(
            "test:1", name="test", host_config={"binds": {}},
            command=["python", "-c", "pass"], working_dir="/app/program",
            environment=["HOME=/ignored", "TEST_PAYLOAD=preserved"])
        state = client.containers[container["Id"]]
        assert not any("BROKER" in key for key in state["env"])
        assert "APPTAINERENV_HOME" not in state["env"]
        assert state["env"]["APPTAINERENV_TEST_PAYLOAD"] == "preserved"
        assert state["args"][state["args"].index("--home") + 1].endswith(":/home/competition")
        assert "--containall" in state["args"]
        assert not any(":/dev/shm" in arg for arg in state["args"])
        scratch_root = Path(state["scratch"].name)
        assert not (scratch_root / "shm").exists()
        # 3. Substitute a local Python command to test actual pipes and exit status.
        state["args"] = [sys.executable, "-c",
                         "import sys; print('out'); print('err', file=sys.stderr); sys.exit(23)"]
        state["env"] = os.environ.copy()
        client.start(container)
        # Deliberately wait before attach: fast exits must retain their logs.
        assert client.wait(container)["StatusCode"] == 23
        chunks = list(client.attach(container))
        assert b"".join(c[0] or b"" for c in chunks) == b"out\n"
        assert b"".join(c[1] or b"" for c in chunks) == b"err\n"
        # 4. Repeated removal must remain safe after process and scratch cleanup.
        client.remove_container(container, force=True)
        client.remove_container(container, force=True)
        assert not scratch_root.exists()
        # 5. Reject image references that are absent from the pre-staged map.
        try:
            client.inspect_image("unapproved:1")
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Unstaged image accepted")
        # 6. Start a parent and child in the same group. If the child survives,
        # it creates this sentinel after forced removal of the group.
        sentinel = Path(directory) / "orphan"
        child_code = f"import time,pathlib; time.sleep(0.3); pathlib.Path({str(sentinel)!r}).touch(); time.sleep(60)"
        parent_code = ("import subprocess,time,sys; "
                       f"subprocess.Popen([sys.executable,'-c',{child_code!r}]); "
                       "print('ready',flush=True); time.sleep(60)")
        process = subprocess.Popen(
            [sys.executable, "-c", parent_code], start_new_session=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Wait until the parent has spawned the child before testing termination.
        assert process.stdout.readline() == b"ready\n"
        scratch = tempfile.TemporaryDirectory()
        client.containers["timeout"] = {"name": "timeout", "process": process,
                                        "scratch": scratch}
        client.remove_container("timeout", force=True)
        assert process.returncode == -signal.SIGKILL
        import time
        # Allow longer than the child's 0.3-second delay, then check no file exists.
        time.sleep(0.5)
        assert not sentinel.exists(), "Subprocess survived group termination"
    print("Apptainer adapter local checks passed")


if __name__ == "__main__":
    self_check()

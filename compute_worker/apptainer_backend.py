import codecs
import hashlib
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
    """Map the Docker API methods used by the Codabench compute worker to Apptainer.

    Only the methods and options required by the worker are implemented.
    This is a partial compatibility layer, not a complete Docker API implementation.
    """

    def __init__(self):
        # Explicit mappings take precedence over downloaded images.
        self.images = json.loads(os.environ.get("APPTAINER_IMAGE_MAP", "{}"))
        self.image_cache = Path(os.environ.get(
            "APPTAINER_CACHEDIR", str(Path.home() / ".apptainer" / "cache")
        )) / "codabench"
        self.containers = {}

    def _image_path(self, image):
        """Resolve a mapped SIF or the cache path for an image reference."""
        mapped = self.images.get(image.removeprefix("docker://"))
        if mapped:
            return Path(mapped)
        reference = image if "://" in image else f"docker://{image}"
        digest = hashlib.sha256(reference.encode()).hexdigest()
        return self.image_cache / f"{digest}.sif"

    def inspect_image(self, image):
        """Return the local SIF path without downloading an image."""
        path = self._image_path(image)
        if not path.is_file():
            raise FileNotFoundError(f"Local Apptainer image not found: {image}")
        return {"Id": str(path)}

    def pull(self, image, **kwargs):
        """Use an explicit SIF mapping or pull an image into the local cache.

        Bare image references use the Docker transport. Yield status dictionaries
        compatible with the compute worker's streaming pull call.
        """
        if self.images.get(image.removeprefix("docker://")):
            self.inspect_image(image)
            yield {"status": "Status: Image is up to date (mapped SIF)"}
            return
        reference = image if "://" in image else f"docker://{image}"
        path = self._image_path(image)
        path.parent.mkdir(parents=True, exist_ok=True)
        yield {"id": image, "status": "Downloading"}
        # Publish only a completed SIF; a failed pull leaves any cached image intact.
        with tempfile.TemporaryDirectory(dir=path.parent, prefix="pull-") as directory:
            temporary = Path(directory) / "image.sif"
            result = subprocess.run(
                ["/usr/bin/apptainer", "pull", str(temporary), reference],
                capture_output=True, text=True,
            )
            if result.returncode:
                raise RuntimeError(
                    f"Apptainer pull failed for {image}: {result.stderr.strip()}"
                )
            temporary.replace(path)
        yield {"id": image, "status": "Pull complete"}

    def create_host_config(self, **kwargs):
        return kwargs

    def create_container(self, image, *, name, host_config, command,
                         working_dir, environment, network_disabled=False, **kwargs):
        """Prepare an Apptainer command and return its Docker-compatible ID.

        Register the command without starting it. The image must be mapped to
        a local SIF or downloaded by pull(). Bind sources stay inside /codabench;
        temporary directories and the execution environment are isolated.
        """
        # Resolve the local image and reject a duplicate container name.
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
            # Translate read/write access; Docker's SELinux label option is omitted.
            mode = "ro" if "ro" in mount.get("mode", "").split(",") else "rw"
            args += ["--bind", f"{source}:{destination}:{mode}"]
        # Enable NVIDIA support when the worker requests GPU access.
        if host_config.get("device_requests"):
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
        # Pass only the required environment to the container process.
        env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp",
               "APPTAINER_TMPDIR": str(root / "tmp")}
        # APPTAINERENV_ explicitly injects the selected values into the payload
        # despite --cleanenv; values baked into the image remain available.
        values = dict(item.split("=", 1) for item in environment)
        # HOME is controlled by --home; Apptainer rejects APPTAINERENV_HOME.
        values.pop("HOME", None)
        # Preserve a host GPU visibility mask when one is configured.
        if host_config.get("device_requests") and "CUDA_VISIBLE_DEVICES" in os.environ:
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
        by the compute worker's streaming attach call. Drain buffered output
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
    """Check container lifecycle and output handling with local Python processes."""
    import sys
    # 1. Register a local SIF mapping to check image lookup and command construction.
    client = APIClient()
    with tempfile.TemporaryDirectory() as directory:
        image = Path(directory) / "image.sif"
        image.touch()
        client.images = {"test:1": str(image)}
        # 2. Check the command descriptor and explicitly selected environment.
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
        # 3. Substitute a local Python command to check output and exit status.
        state["args"] = [sys.executable, "-c",
                         "import sys; print('out'); print('err', file=sys.stderr); sys.exit(23)"]
        state["env"] = os.environ.copy()
        client.start(container)
        # Deliberately wait before attach: fast exits must retain their logs.
        assert client.wait(container)["StatusCode"] == 23
        chunks = list(client.attach(container))
        assert b"".join(c[0] or b"" for c in chunks) == b"out\n"
        assert b"".join(c[1] or b"" for c in chunks) == b"err\n"
        # 4. Check repeated removal after process and temporary directory cleanup.
        client.remove_container(container, force=True)
        client.remove_container(container, force=True)
        assert not scratch_root.exists()
        # 5. Inspection must not download an image that is unavailable locally.
        try:
            client.inspect_image("unapproved:1")
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Missing local image accepted")
        # 6. Check image pulls without invoking Apptainer or contacting a registry.
        from unittest.mock import patch
        client.image_cache = Path(directory) / "cache"

        def fake_pull(args, **kwargs):
            Path(args[2]).write_bytes(b"SIF")
            return subprocess.CompletedProcess(args, 0, "", "")

        with patch.object(subprocess, "run", side_effect=fake_pull) as run:
            assert list(client.pull("test:1"))
            run.assert_not_called()
            assert list(client.pull("download:1"))[-1]["status"] == "Pull complete"
            assert run.call_args.args[0][-1] == "docker://download:1"
        cached = Path(client.inspect_image("docker://download:1")["Id"])
        assert cached.read_bytes() == b"SIF"
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess(
            [], 1, "", "pull failed"
        )):
            try:
                list(client.pull("download:1"))
            except RuntimeError as error:
                assert "pull failed" in str(error)
            else:
                raise AssertionError("Failed image pull accepted")
        assert cached.read_bytes() == b"SIF"
        assert list(client.image_cache.iterdir()) == [cached]
        # 7. Start a parent and child in the same group. If the child survives,
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

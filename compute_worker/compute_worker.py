import asyncio
import glob
import hashlib
import json
import os
import shutil
import signal
import socket
import tempfile
import time
import uuid
from shutil import make_archive
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlretrieve
from zipfile import ZipFile, BadZipFile
import docker
from rich.progress import Progress
from rich.pretty import pprint
import requests

import websockets
import yaml
from billiard.exceptions import SoftTimeLimitExceeded
from celery import Celery, shared_task, utils
from kombu import Queue, Exchange
from urllib3 import Retry

# This is only needed for the pytests to pass
import sys

sys.path.append("/app/src/settings/")

from celery import signals
import logging

logger = logging.getLogger(__name__)
from logs_loguru import configure_logging, colorize_run_args
import json


# -----------------------------------------------
# Logging
# -----------------------------------------------
configure_logging(
    os.environ.get("LOG_LEVEL", "INFO"), os.environ.get("SERIALIZED", "false")
)

# -----------------------------------------------
# Initialize Docker or Podman depending on .env
# -----------------------------------------------
if os.environ.get("USE_GPU", "false").lower() == "true":
    logger.info(
        "Using "
        + os.environ.get("CONTAINER_ENGINE_EXECUTABLE", "docker").upper()
        + "with GPU capabilites : "
        + os.environ.get("GPU_DEVICE", "nvidia.com/gpu=all")
    )
else:
    logger.info(
        "Using "
        + os.environ.get("CONTAINER_ENGINE_EXECUTABLE", "docker").upper()
        + " without GPU capabilities"
    )

if os.environ.get("CONTAINER_ENGINE_EXECUTABLE", "docker").lower() == "docker":
    client = docker.APIClient(
        base_url=os.environ.get("CONTAINER_SOCKET", "unix:///var/run/docker.sock"),
        version="auto",
    )
elif os.environ.get("CONTAINER_ENGINE_EXECUTABLE").lower() == "podman":
    client = docker.APIClient(
        base_url=os.environ.get(
            "CONTAINER_SOCKET", "unix:///run/user/1000/podman/podman.sock"
        ),
        version="auto",
    )


# -----------------------------------------------
# Show Progress bar on downloading images
# -----------------------------------------------
tasks = {}


def show_progress(line, progress):
    try:
        if "Status: Image is up to date" in line["status"]:
            logger.info(line["status"])

        completed = False
        if line["status"] == "Download complete":
            description = (
                f"[blue][Download complete, waiting for extraction  {line['id']}]"
            )
            completed = True
        elif line["status"] == "Downloading":
            description = f"[bold][Downloading {line['id']}]"
        elif line["status"] == "Pull complete":
            description = f"[green][Extraction complete  {line['id']}]"
            completed = True
        elif line["status"] == "Extracting":
            description = f"[blue][Extracting  {line['id']}]"

        else:
            # skip other statuses, but show extraction progress
            return

        task_id = line["id"]
        if task_id not in tasks.keys():
            if completed:
                # some layers are really small that they download immediately without showing
                # anything as Downloading in the stream.
                # For that case, show a completed progress bar
                tasks[task_id] = progress.add_task(
                    description, total=100, completed=100
                )
            else:
                tasks[task_id] = progress.add_task(
                    description, total=line["progressDetail"]["total"]
                )
        else:
            if completed:
                # due to the stream, the Download complete output can happen before the Downloading
                # bar outputs the 100%. So when we detect that the download is in fact complete,
                # update the progress bar to show 100%
                progress.update(
                    tasks[task_id], description=description, total=100, completed=100
                )
            else:
                progress.update(
                    tasks[task_id],
                    completed=line["progressDetail"]["current"],
                    total=line["progressDetail"]["total"],
                )
    except Exception as e:
        logger.error("There was an error showing the progress bar")
        logger.error(e)


# -----------------------------------------------
# Celery + Rabbit MQ
# -----------------------------------------------
@signals.setup_logging.connect
def setup_celery_logging(**kwargs):
    pass


# Init celery + rabbit queue definitions
app = Celery()
app.config_from_object("celery_config")  # grabs celery_config.py
app.conf.task_queues = [
    # Mostly defining queue here so we can set x-max-priority
    Queue(
        "compute-worker",
        Exchange("compute-worker"),
        routing_key="compute-worker",
        queue_arguments={"x-max-priority": 10},
    ),
]
# -----------------------------------------------
# Directories
# -----------------------------------------------
# Setup base directories used by all submissions
# note: we need to pass this directory to docker/podman so it knows where to store things!
HOST_DIRECTORY = os.environ.get("HOST_DIRECTORY", "/tmp/codabench/")
BASE_DIR = "/codabench/"  # base directory inside the container
CACHE_DIR = os.path.join(BASE_DIR, "cache")
MAX_CACHE_DIR_SIZE_GB = float(os.environ.get("MAX_CACHE_DIR_SIZE_GB", 10))


# -----------------------------------------------
# Submission status
# -----------------------------------------------
# Status options for submissions
STATUS_NONE = "None"
STATUS_SUBMITTING = "Submitting"
STATUS_SUBMITTED = "Submitted"
STATUS_PREPARING = "Preparing"
STATUS_RUNNING = "Running"
STATUS_SCORING = "Scoring"
STATUS_FINISHED = "Finished"
STATUS_FAILED = "Failed"
AVAILABLE_STATUSES = (
    STATUS_NONE,
    STATUS_SUBMITTING,
    STATUS_SUBMITTED,
    STATUS_PREPARING,
    STATUS_RUNNING,
    STATUS_SCORING,
    STATUS_FINISHED,
    STATUS_FAILED,
)


# -----------------------------------------------
# Exceptions
# -----------------------------------------------
class SubmissionException(Exception):
    pass


class DockerImagePullException(Exception):
    pass


class ExecutionTimeLimitExceeded(Exception):
    pass


# -----------------------------------------------------------------------------
# The main compute worker entrypoint, this is how a job is ran at the highest
# level.
# -----------------------------------------------------------------------------
@shared_task(name="compute_worker_run")
def run_wrapper(run_args):
    logger.info(f"Received run arguments: \n {colorize_run_args(json.dumps(run_args))}")
    run = Run(run_args)

    try:
        run.prepare()
        run.start()
        if run.is_scoring:
            run.push_scores()
        run.push_output()
    except DockerImagePullException as e:
        run._update_status(STATUS_FAILED, str(e))
    except SubmissionException as e:
        run._update_status(STATUS_FAILED, str(e))
    except SoftTimeLimitExceeded:
        run._update_status(STATUS_FAILED, "Soft time limit exceeded!")
    finally:
        run.clean_up()


def replace_legacy_metadata_command(
    command, kind, is_scoring, ingestion_only_during_scoring=False
):
    vars_to_replace = [
        ("$input", "/app/input_data" if kind == "ingestion" else "/app/input"),
        ("$output", "/app/output"),
        (
            "$program",
            "/app/ingestion_program"
            if ingestion_only_during_scoring and is_scoring
            else "/app/program",
        ),
        ("$ingestion_program", "/app/program"),
        ("$hidden", "/app/input/ref"),
        ("$shared", "/app/shared"),
        ("$submission_program", "/app/ingested_program"),
        # for v1.8 compatibility
        ("$tmp", "/app/output"),
        ("$predictions", "/app/input/res" if is_scoring else "/app/output"),
    ]
    for var_string, var_replacement in vars_to_replace:
        command = command.replace(var_string, var_replacement)
    return command


def md5(filename):
    """Given some file return its md5, works well on large files"""
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_folder_size_in_gb(folder):
    if not os.path.exists(folder):
        return 0
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        path = os.path.join(folder, item)
        if os.path.isfile(path):
            total_size += os.path.getsize(path)
        elif os.path.isdir(path):
            total_size += get_folder_size_in_gb(path)
    return total_size / 1000 / 1000 / 1000  # GB: decimal system (1000^3)


def delete_files_in_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def is_valid_zip(zip_path):
    # Check zip integrity
    try:
        with ZipFile(zip_path, "r") as zf:
            return zf.testzip() is None
    except BadZipFile:
        return False


def alarm_handler(signum, frame):
    raise ExecutionTimeLimitExceeded


# -----------------------------------------------
# Class Run
# Responsible for running a submission inside a docker/podman container
# -----------------------------------------------
class Run:
    """A "Run" in Codabench is composed of some program, some data to work with, and some signed URLs to upload results
    to. There is also a secret key to do special commands for just this submission.

    Some example API's you can hit using this secret key are:

        push_scores

        (maybe later:
            get previous submission
            get sibling submission
            get top submission
            get some different dataset
            post results to twitter)
    """

    def __init__(self, run_args):
        # Directories for the run
        self.watch = True
        self.completed_program_counter = 0
        self.root_dir = tempfile.mkdtemp(dir=BASE_DIR)
        self.bundle_dir = os.path.join(self.root_dir, "bundles")
        self.input_dir = os.path.join(self.root_dir, "input")
        self.output_dir = os.path.join(self.root_dir, "output")
        self.data_dir = os.path.join(
            HOST_DIRECTORY, "data"
        )  # absolute path to data in the host
        self.logs = {}

        # Details for submission
        self.is_scoring = run_args["is_scoring"]
        self.user_pk = run_args["user_pk"]
        self.submission_id = run_args["id"]
        self.submissions_api_url = run_args["submissions_api_url"]
        self.container_image = run_args["docker_image"]
        self.secret = run_args["secret"]
        self.prediction_result = run_args["prediction_result"]
        self.scoring_result = run_args.get("scoring_result")
        self.execution_time_limit = run_args["execution_time_limit"]
        # stdout and stderr
        self.stdout, self.stderr, self.ingestion_stdout, self.ingestion_stderr = (
            self._get_stdout_stderr_file_names(run_args)
        )
        self.ingestion_container_name = uuid.uuid4()
        self.program_container_name = uuid.uuid4()
        self.program_data = run_args.get("program_data")
        self.ingestion_program_data = run_args.get("ingestion_program")
        self.input_data = run_args.get("input_data")
        self.reference_data = run_args.get("reference_data")
        self.ingestion_only_during_scoring = run_args.get(
            "ingestion_only_during_scoring"
        )
        self.detailed_results_url = run_args.get("detailed_results_url")

        # During prediction program will be the submission program, during scoring it will be the
        # scoring program
        self.program_exit_code = None
        self.ingestion_program_exit_code = None

        self.program_elapsed_time = None
        self.ingestion_elapsed_time = None

        # Socket connection to stream output of submission
        submission_api_url_parsed = urlparse(self.submissions_api_url)
        websocket_host = submission_api_url_parsed.netloc
        websocket_scheme = "ws" if submission_api_url_parsed.scheme == "http" else "wss"
        self.websocket_url = f"{websocket_scheme}://{websocket_host}/submission_input/{self.user_pk}/{self.submission_id}/{self.secret}/"

        # Nice requests adapter with generous retries/etc.
        self.requests_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            max_retries=Retry(
                total=3,
                backoff_factor=1,
            )
        )
        self.requests_session.mount("http://", adapter)
        self.requests_session.mount("https://", adapter)

    async def watch_detailed_results(self):
        """Watches files alongside scoring + program containers, currently only used
        for detailed_results.html"""
        if not self.detailed_results_url:
            return
        file_path = self.get_detailed_results_file_path()
        last_modified_time = None
        start = time.time()
        expiration_seconds = 60

        while self.watch and self.completed_program_counter < 2:
            if file_path:
                new_time = os.path.getmtime(file_path)
                if new_time != last_modified_time:
                    last_modified_time = new_time
                    await self.send_detailed_results(file_path)
            else:
                logger.info(time.time() - start)
                if time.time() - start > expiration_seconds:
                    timeout_error_message = (
                        "WARNING: Detailed results not written before the execution."
                    )
                    logger.warning(timeout_error_message)
            await asyncio.sleep(5)
            file_path = self.get_detailed_results_file_path()
        else:
            # make sure we always send the final version of the file
            if file_path:
                await self.send_detailed_results(file_path)

    def get_detailed_results_file_path(self):
        default_detailed_results_path = os.path.join(
            self.output_dir, "detailed_results.html"
        )
        if os.path.exists(default_detailed_results_path):
            return default_detailed_results_path
        else:
            # v1.5 compatibility - get the first html file if detailed_results.html doesn't exists
            html_files = glob.glob(os.path.join(self.output_dir, "*.html"))
            if html_files:
                return html_files[0]

    async def send_detailed_results(self, file_path):
        logger.info(
            f"Updating detailed results {file_path} - {self.detailed_results_url}"
        )
        self._put_file(
            self.detailed_results_url, file=file_path, content_type="text/html"
        )
        websocket_url = f"{self.websocket_url}?kind=detailed_results"
        logger.info(f"Connecting to {websocket_url} for detailed results")
        # Wrap this with a Try ... Except otherwise a failure here will make the submission get stuck on Running
        try:
            websocket = await asyncio.wait_for(
                websockets.connect(websocket_url), timeout=30.0
            )
            await websocket.send(
                json.dumps(
                    {
                        "kind": "detailed_result_update",
                    }
                )
            )
        except Exception as e:
            logger.error("This error might result in a Execution Time Exceeded error" + e)
            if os.environ.get("LOG_LEVEL", "info").lower() == "debug":
                logger.exception(e)

    def _get_stdout_stderr_file_names(self, run_args):
        # run_args should be the run_args argument passed to __init__ from the run_wrapper.
        if not self.is_scoring:
            DETAILED_OUTPUT_NAMES = [
                "prediction_stdout",
                "prediction_stderr",
                "prediction_ingestion_stdout",
                "prediction_ingestion_stderr",
            ]
        else:
            DETAILED_OUTPUT_NAMES = [
                "scoring_stdout",
                "scoring_stderr",
                "scoring_ingestion_stdout",
                "scoring_ingestion_stderr",
            ]
        return [run_args[name] for name in DETAILED_OUTPUT_NAMES]

    def _update_submission(self, data):
        url = f"{self.submissions_api_url}/submissions/{self.submission_id}/"
        data["secret"] = self.secret

        logger.info(f"Updating submission @ {url} with data = {data}")

        resp = self.requests_session.patch(url, data, timeout=150)
        if resp.status_code == 200:
            logger.info("Submission updated successfully!")
        else:
            logger.error(
                f"Submission patch failed with status = {resp.status_code}, and response = \n{resp.content}"
            )
            raise SubmissionException("Failure updating submission data.")

    def _update_status(self, status, extra_information=None):
        if status not in AVAILABLE_STATUSES:
            raise SubmissionException(
                f"Status '{status}' is not in available statuses: {AVAILABLE_STATUSES}"
            )

        data = {
            "status": status,
            "status_details": extra_information,
        }

        # TODO: figure out if we should pull this task code later(submission.task should always be set)
        # When we start
        # if status == STATUS_SCORING:
        #     data.update({
        #         "task_pk": self.task_pk,
        #     })
        self._update_submission(data)

    def _get_container_image(self, image_name):
        logger.info("Running pull for image: {}".format(image_name))
        retries, max_retries = (0, 3)
        while retries < max_retries:
            try:
                with Progress() as progress:
                    resp = client.pull(image_name, stream=True, decode=True)
                    for line in resp:
                        show_progress(line, progress)
                    break  # Break if the loop is successful to exit "with Progress() as progress"

            except (docker.errors.APIError, Exception) as pull_error:
                retries += 1
                if retries >= max_retries:
                    logger.error(
                        "There was a problem pulling the image : " + str(pull_error)
                    )
                    # Prepare data to be sent to submissions api
                    docker_pull_fail_data = {
                        "type": "Docker_Image_Pull_Fail",
                        "error_message": pull_error,
                        "is_scoring": self.is_scoring,
                    }
                    # Send data to be written to ingestion logs
                    self._update_submission(docker_pull_fail_data)
                    # Send error through web socket to the frontend
                    asyncio.run(self._send_data_through_socket(str(pull_error)))
                    raise DockerImagePullException(
                        f"Pull for {image_name} failed! Check the logs for more information"
                    )
                else:
                    logger.warning("Failed. Retrying in 5 seconds...")
                    time.sleep(5)  # Wait 5 seconds before retrying

    async def _send_data_through_socket(self, error_message):
        """
        This function gets an error messages and sends it through a web socket. This function is used for sending
        - Docker image pull failure logs
        - Execution time limit exceeded logs
        """
        # Create a unique websocket URL for error messages
        websocket_url = f"{self.websocket_url}?kind=error_logs"
        logger.info(f"Connecting to {websocket_url} to send error message")

        logger.info(f"Connecting to {websocket_url} to send docker image pull error")

        # connect to web socket
        websocket = await asyncio.wait_for(
            websockets.connect(websocket_url), timeout=10.0
        )

        # define websocket errors
        websocket_errors = (
            socket.gaierror,
            websockets.WebSocketException,
            websockets.ConnectionClosedError,
            ConnectionRefusedError,
        )

        try:
            # send message
            await websocket.send(
                json.dumps({"kind": "stderr", "message": error_message})
            )

        except websocket_errors:
            # handle websocket errors
            logger.error("Error sending failed through websocket")
            try:
                await websocket.close()
            except Exception as e:
                logger.error(e)
        else:
            # no error in websocket message sending
            logger.info("Error sent successfully through websocket")

        logger.info(f"Disconnecting from websocket {websocket_url}")

        # close websocket
        await websocket.close()

    def _get_bundle(self, url, destination, cache=True):
        """Downloads zip from url and unzips into destination. If cache=True then url is hashed and checked
        against existence in CACHE_DIR/<hashed_url> and only downloaded if needed. Cache size is checked
        during the prepare step and cleared if it's over MAX_CACHE_DIR_SIZE_GB.

        :returns zip file path"""
        logger.info(f"Getting bundle {url} to unpack @ {destination}")
        download_needed = True

        # Try to find the bundle in the cache of the worker
        if cache:
            # Hash url and download it if it doesn't exist
            url_without_params = url.split("?")[0]
            url_hash = hashlib.sha256(url_without_params.encode("utf8")).hexdigest()
            bundle_file = os.path.join(CACHE_DIR, url_hash)
            download_needed = not os.path.exists(bundle_file)
        else:
            if not os.path.exists(self.bundle_dir):
                os.mkdir(self.bundle_dir)
            bundle_file = tempfile.NamedTemporaryFile(
                dir=self.bundle_dir, delete=False
            ).name

        # Fetch and extract
        retries, max_retries = (0, 10)
        while retries < max_retries:
            if download_needed:
                try:
                    # Download the bundle
                    urlretrieve(url, bundle_file)
                except HTTPError:
                    raise SubmissionException(
                        f"Problem fetching {url} to put in {destination}"
                    )
            try:
                # Extract the contents to destination directory
                with ZipFile(bundle_file, "r") as z:
                    z.extractall(os.path.join(self.root_dir, destination))
                break  # Break if the loop is successful
            except BadZipFile:
                retries += 1
                if retries >= max_retries:
                    raise  # Re-raise the last caught BadZipFile exception
                else:
                    logger.warning("Failed. Retrying in 60 seconds...")
                    time.sleep(60)  # Wait 60 seconds before retrying
        # Return the zip file path for other uses, e.g. for creating a MD5 hash to identify it
        return bundle_file

    async def _run_container_engine_cmd(self, container, kind):
        """This runs a command and asynchronously writes the data to both a storage file
        and a socket

        :param engine_cmd: the list of container engine command arguments
        :param kind: either 'ingestion' or 'program'
        :return:
        """

        # Creating this and setting 2 values to None in case there is not enough time for the worker to get logs, otherwise we will have errors later on
        logs_Unified = [None, None]

        # Create a websocket to send the logs in real time to the codabench instance
        # We need to set a timeout for the websocket connection otherwise the program will get stuck if he websocket does not connect.
        try:
            websocket_url = f"{self.websocket_url}?kind={kind}"
            logger.debug(
                "Connecting to "
                + websocket_url
                + "for container "
                + str(container.get("Id"))
            )
            websocket = await asyncio.wait_for(
                websockets.connect(websocket_url), timeout=10.0
            )
            logger.debug(
                "connected to "
                + str(websocket_url)
                + "for container "
                + str(container.get("Id"))
            )
        except Exception as e:
            logger.error(
                "There was an error trying to connect to the websocket on the codabench instance"
                + e
            )
            if os.environ.get("LOG_LEVEL", "info").lower() == "debug":
                logger.exception(e)

        start = time.time()

        # Stream the logs of competition container while also sending them to the codabench instance
        try:
            logger.debug("Starting container " + container.get("Id"))
            client.start(container=container.get("Id"))
            logger.debug(
                "Attaching to started container to get the logs :" + container.get("Id")
            )
            container_LogsDemux = client.attach(
                container, demux=True, stream=True, logs=True
            )

            # If we enter the for loop after the container exited, the program will get stuck
            if (
                client.inspect_container(container)["State"]["Status"].lower()
                == "running"
            ):
                logger.debug(
                    "Show the logs and stream them to codabench " + container.get("Id")
                )
                for log in container_LogsDemux:
                    if str(log[0]) != "None":
                        logger.info(log[0].decode())
                        try:
                            await websocket.send(
                                json.dumps({"kind": kind, "message": log[0].decode()})
                            )
                        except Exception as e:
                            logger.error(e)

                    elif str(log[1]) != "None":
                        logger.error(log[1].decode())
                        try:
                            await websocket.send(
                                json.dumps({"kind": kind, "message": log[1].decode()})
                            )
                        except Exception as e:
                            logger.error(e)

        except (docker.errors.NotFound, docker.errors.APIError) as e:
            logger.error(e)
        except Exception as e:
            logger.error(
                "There was an error while starting the container and getting the logs"
                + e
            )
            if os.environ.get("LOG_LEVEL", "info").lower() == "debug":
                logger.exception(e)

        # Get the return code of the competition container once done
        try:
            # Gets the logs of the container, sperating stdout and stderr (first and second position) thanks for demux=True
            logs_Unified = client.attach(container, logs=True, demux=True)
            return_Code = client.wait(container)
            logger.debug(
                f"WORKER_MARKER: Disconnecting from {websocket_url}, program counter = {self.completed_program_counter}"
            )
            await websocket.close()
            client.remove_container(container, force=True)

            logger.debug(
                "Container "
                + container.get("Id")
                + "exited with status code : "
                + str(return_Code["StatusCode"])
            )

        except (
            requests.exceptions.ReadTimeout,
            docker.errors.APIError,
            Exception,
        ) as e:
            logger.error(e)
            return_Code = {"StatusCode": e}

        self.logs[kind] = {
            "returncode": return_Code["StatusCode"],
            "start": start,
            "end": None,
            "stdout": {
                "data": logs_Unified[0],
                "stream": logs_Unified[0],
                "continue": True,
                "location": self.stdout if kind == "program" else self.ingestion_stdout,
            },
            "stderr": {
                "data": logs_Unified[1],
                "stream": logs_Unified[1],
                "continue": True,
                "location": self.stderr if kind == "program" else self.ingestion_stderr,
            },
        }

        self.logs[kind]["end"] = time.time()

        # Communicate that the program is closing
        self.completed_program_counter += 1

    def _get_host_path(self, *paths):
        """Turns an absolute path inside our container, into what the path
        would be on the host machine. We also ensure that the directory exists,
        docker will create if necessary, but other container engines such as
        podman may not."""
        # Take our list of paths and smash 'em together
        path = os.path.join(*paths)

        # pull front of path, which points to the location inside the container
        path = path[len(BASE_DIR) :]

        # add host to front, so when we run commands in the container on the host they
        # can be seen properly
        path = os.path.join(HOST_DIRECTORY, path)

        # Create if necessary
        os.makedirs(path, exist_ok=True)

        return path

    async def _run_program_directory(self, program_dir, kind):
        """
        Function responsible for running program directory

        Args:
            - program_dir : can be either ingestion program or program/submission
            - kind : either `program` or `ingestion`
        """
        # If the directory doesn't even exist, move on
        if not os.path.exists(program_dir):
            logger.warning(f"{program_dir} not found, no program to execute")

            # Communicate that the program is closing
            self.completed_program_counter += 1
            return

        if os.path.exists(os.path.join(program_dir, "metadata.yaml")):
            metadata_path = "metadata.yaml"
        elif os.path.exists(os.path.join(program_dir, "metadata")):
            metadata_path = "metadata"
        else:
            # Display a warning in logs when there is no metadata file in submission/program dir
            if kind == "program":
                logger.warning(
                    "Program directory missing metadata, assuming it's going to be handled by ingestion"
                )
                # Copy submission files into prediction output
                # This is useful for results submissions but wrongly uses storage
                shutil.copytree(program_dir, self.output_dir)
                return
            else:
                raise SubmissionException(
                    "Program directory missing 'metadata.yaml/metadata'"
                )

        logger.info(f"Metadata path is {os.path.join(program_dir, metadata_path)}")
        with open(os.path.join(program_dir, metadata_path), "r") as metadata_file:
            try:  # try to find a command in the metadata, in other cases set metadata to None
                metadata = yaml.load(metadata_file.read(), Loader=yaml.FullLoader)
                logger.info(f"Metadata contains:\n {metadata}")
                if isinstance(metadata, dict):  # command found
                    command = metadata.get("command")
                else:
                    command = None
            except yaml.YAMLError as e:
                logger.error("Error parsing YAML file: ", e)
                print("Error parsing YAML file: ", e)
                command = None
            if not command and kind == "ingestion":
                raise SubmissionException(
                    "Program directory missing 'command' in metadata"
                )
            elif not command:
                logger.warning(
                    f"Warning: {program_dir} has no command in metadata, continuing anyway "
                    f"(may be meant to be consumed by an ingestion program)"
                )
                return
        volumes_host = [
            self._get_host_path(program_dir),
            self._get_host_path(self.output_dir),
            self.data_dir,
        ]
        volumes_config = {
            volumes_host[0]: {
                "bind": "/app/program",
                "mode": "z",
            },
            volumes_host[1]: {
                "bind": "/app/output",
                "mode": "z",
            },
            volumes_host[2]: {
                "bind": "/app/data",
                "mode": "ro",
            },
        }

        if kind == "ingestion":
            # program here is either scoring program or submission, depends on if this ran during Prediction or Scoring
            if self.ingestion_only_during_scoring and self.is_scoring:
                # submission program moved to 'input/res' with shutil.move() above
                ingested_program_location = "input/res"
            else:
                ingested_program_location = "program"
            volumes_host.extend(
                [self._get_host_path(self.root_dir, ingested_program_location)]
            )
            tempvolumeConfig = {
                volumes_host[-1]: {
                    "bind": "/app/ingested_program",
                }
            }
            volumes_config.update(tempvolumeConfig)

        if self.is_scoring:
            # For scoring programs, we want to have a shared directory just in case we have an ingestion program.
            # This will add the share dir regardless of ingestion or scoring, as long as we're `is_scoring`
            volumes_host.extend([self._get_host_path(self.root_dir, "shared")])
            tempvolumeConfig = {
                volumes_host[-1]: {
                    "bind": "/app/shared",
                }
            }
            volumes_config.update(tempvolumeConfig)

            # Input from submission (or submission + ingestion combo)
            volumes_host.extend([self._get_host_path(self.input_dir)])
            tempvolumeConfig = {
                volumes_host[-1]: {
                    "bind": "/app/input",
                }
            }
            volumes_config.update(tempvolumeConfig)

        if self.input_data:
            volumes_host.extend([self._get_host_path(self.root_dir, "input_data")])
            tempvolumeConfig = {
                volumes_host[-1]: {
                    "bind": "/app/input_data",
                }
            }
            volumes_config.update(tempvolumeConfig)

        # Handle Legacy competitions by replacing anything in the run command
        command = replace_legacy_metadata_command(
            command=command,
            kind=kind,
            is_scoring=self.is_scoring,
            ingestion_only_during_scoring=self.ingestion_only_during_scoring,
        )

        cap_drop_list = [
            "AUDIT_WRITE",
            "CHOWN",
            "DAC_OVERRIDE",
            "FOWNER",
            "FSETID",
            "KILL",
            "MKNOD",
            "NET_BIND_SERVICE",
            "NET_RAW",
            "SETFCAP",
            "SETGID",
            "SETPCAP",
            "SETUID",
            "SYS_CHROOT",
        ]
        # Configure whether or not we use the GPU. Also setting auto_remove to False because
        if os.environ.get("CONTAINER_ENGINE_EXECUTABLE", "docker").lower() == "docker":
            security_options = ["no-new-privileges"]
        else:
            security_options = ["label=disable"]
        # Setting the device ID like this allows users to specify which gpu to use in the .env file, with all being the default if no value is given
        device_id = [os.environ.get("GPU_DEVICE", "nvidia.com/gpu=all")]
        if os.environ.get("USE_GPU", "false").lower() == "true":
            logger.info("Running the container with GPU capabilities")
            host_config = client.create_host_config(
                auto_remove=False,
                cap_drop=cap_drop_list,
                binds=volumes_config,
                userns_mode="host",
                security_opt=security_options,
                device_requests=[
                    {
                        "Driver": "cdi",
                        "DeviceIDs": device_id,
                    },
                ],
            )
        else:
            host_config = client.create_host_config(
                auto_remove=False,
                cap_drop=cap_drop_list,
                binds=volumes_config,
                userns_mode="host",
                security_opt=security_options,
            )

        logger.info("Running container with command " + command)
        container_name = (
            self.ingestion_container_name
            if kind == "ingestion"
            else self.program_container_name
        )
        container = client.create_container(
            self.container_image,
            name=container_name,
            host_config=host_config,
            detach=False,
            volumes=volumes_host,
            command=command,
            working_dir="/app/program",
            environment=["PYTHONUNBUFFERED=1"],
        )
        logger.debug("Created container : " + str(container))
        logger.info("Volume configuration of the container: ")
        pprint(volumes_config)
        # This runs the container engine command and asynchronously passes data back via websocket
        try:
            return await self._run_container_engine_cmd(container, kind=kind)
        except Exception as e:
            logger.error(e)
            if os.environ.get("LOG_LEVEL", "info").lower() == "debug":
                logger.exception(e)

    def _put_dir(self, url, directory):
        """Zip the directory and send it to the given URL using _put_file."""
        logger.info("Putting dir %s in %s" % (directory, url))
        retries, max_retries = (0, 3)
        while retries < max_retries:
            # Zip the directory
            start_time = time.time()
            zip_path = make_archive(
                os.path.join(self.root_dir, str(uuid.uuid4())), "zip", directory
            )
            duration = time.time() - start_time
            logger.info(f"Time needed to zip archive: {duration} seconds.")
            if is_valid_zip(zip_path):  # Check zip integrity
                self._put_file(url, file=zip_path)  # Send the file
                break  # Leave the loop in case of success
            else:
                retries += 1
                if retries >= max_retries:
                    raise Exception("ZIP file is corrupted or incomplete.")
                else:
                    logger.info("Failed. Retrying in 30 seconds...")
                    time.sleep(30)  # Wait 30 seconds before retrying

    def _put_file(self, url, file=None, raw_data=None, content_type="application/zip"):
        """Send the file in the storage."""
        if file and raw_data:
            raise Exception("Cannot put both a file and raw_data")

        headers = {
            # For Azure only, other systems ignore these headers
            "x-ms-blob-type": "BlockBlob",
            "x-ms-version": "2018-03-28",
        }
        if content_type:
            headers["Content-Type"] = content_type
        if file:
            logger.info("Putting file %s in %s" % (file, url))
            data = open(file, "rb")
            headers["Content-Length"] = str(os.path.getsize(file))
        elif raw_data:
            logger.info("Putting raw data %s in %s" % (raw_data, url))
            data = raw_data
        else:
            raise SubmissionException(
                "Must provide data, both file and raw_data cannot be empty"
            )

        resp = self.requests_session.put(
            url,
            data=data,
            headers=headers,
        )
        logger.info("*** PUT RESPONSE: ***")
        logger.info(f"response: {resp}")
        logger.info(f"content: {resp.content}")

    def _prep_cache_dir(self, max_size=MAX_CACHE_DIR_SIZE_GB):
        if not os.path.exists(CACHE_DIR):
            os.mkdir(CACHE_DIR)
        logger.info("Checking if cache directory needs to be pruned...")
        if get_folder_size_in_gb(CACHE_DIR) > max_size:
            logger.info("Pruning cache directory")
            delete_files_in_folder(CACHE_DIR)
        else:
            logger.info("Cache directory does not need to be pruned!")

    def prepare(self):
        if not self.is_scoring:
            # Only during prediction step do we want to announce "preparing"
            self._update_status(STATUS_PREPARING)

        # Setup cache and prune if it's out of control
        self._prep_cache_dir()

        # A run *may* contain the following bundles, let's grab them and dump them in the appropriate
        # sub folder.
        bundles = [
            # (url to file, relative folder destination)
            (self.program_data, "program"),
            (self.ingestion_program_data, "ingestion_program"),
            (self.input_data, "input_data"),
            (self.reference_data, "input/ref"),
        ]
        if self.is_scoring:
            # Send along submission result so scoring_program can get access
            bundles += [(self.prediction_result, "input/res")]

        for url, path in bundles:
            if url is not None:
                # At the moment let's just cache input & reference data
                cache_this_bundle = path in ("input_data", "input/ref")
                zip_file = self._get_bundle(url, path, cache=cache_this_bundle)

                # TODO: When we have `is_scoring_only` this needs to change...
                if url == self.program_data and not self.is_scoring:
                    # We want to get a checksum of submissions so we can check if they are
                    # a solution, or maybe match them against other submissions later
                    logger.info(f"Beginning MD5 checksum of submission: {zip_file}")
                    checksum = md5(zip_file)
                    logger.info(f"Checksum result: {checksum}")
                    self._update_submission({"md5": checksum})

        # For logging purposes let's dump file names
        for filename in glob.iglob(self.root_dir + "**/*.*", recursive=True):
            logger.info(filename)

        # Before the run starts we want to download images, they may take a while to download
        # and to do this during the run would subtract from the participants time.
        self._get_container_image(self.container_image)

    def start(self):
        hostname = utils.nodenames.gethostname()
        if self.is_scoring:
            self._update_status(
                STATUS_RUNNING, extra_information=f"scoring_hostname-{hostname}"
            )
        else:
            self._update_status(
                STATUS_RUNNING, extra_information=f"ingestion_hostname-{hostname}"
            )
        program_dir = os.path.join(self.root_dir, "program")
        ingestion_program_dir = os.path.join(self.root_dir, "ingestion_program")

        logger.info("Running scoring program, and then ingestion program")
        loop = asyncio.new_event_loop()
        gathered_tasks = asyncio.gather(
            self._run_program_directory(program_dir, kind="program"),
            self._run_program_directory(ingestion_program_dir, kind="ingestion"),
            self.watch_detailed_results(),
            loop=loop,
        )

        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(self.execution_time_limit)
        try:
            loop.run_until_complete(gathered_tasks)
        except ExecutionTimeLimitExceeded:
            error_message = f"Execution Time Limit exceeded. Limit was {self.execution_time_limit} seconds"
            logger.error(error_message)
            # Prepare data to be sent to submissions api
            execution_time_limit_exceeded_data = {
                "type": "Execution_Time_Limit_Exceeded",
                "error_message": error_message,
                "is_scoring": self.is_scoring,
            }
            # Some cleanup
            for kind, logs in self.logs.items():
                containers_to_kill = []
                containers_to_kill.append(self.ingestion_container_name)
                containers_to_kill.append(self.program_container_name)
                logger.debug(
                    "Trying to kill and remove container " + str(containers_to_kill)
                )
                for container in containers_to_kill:
                    try:
                        client.remove_container(str(container), force=True)
                    except docker.errors.APIError as e:
                        logger.error(e)
                    except Exception as e:
                        logger.error(
                            "There was a problem killing " + str(containers_to_kill) + e
                        )
                        if os.environ.get("LOG_LEVEL", "info").lower() == "debug":
                            logger.exception(e)
            # Send data to be written to ingestion/scoring std_err
            self._update_submission(execution_time_limit_exceeded_data)
            # Send error through web socket to the frontend
            asyncio.run(self._send_data_through_socket(error_message))
            raise SubmissionException(error_message)
        finally:
            self.watch = False
            for kind, logs in self.logs.items():
                if logs["end"] is not None:
                    elapsed_time = logs["end"] - logs["start"]
                else:
                    elapsed_time = self.execution_time_limit
                return_code = logs["returncode"]
                if return_code is None:
                    logger.warning("No return code from Process. Killing it")
                    if kind == "ingestion":
                        containers_to_kill = self.ingestion_container_name
                    else:
                        containers_to_kill = self.program_container_name
                    try:
                        client.kill(containers_to_kill)
                        client.remove_container(containers_to_kill, force=True)
                    except docker.errors.APIError as e:
                        logger.error(e)
                    except Exception as e:
                        logger.error(
                            "There was a problem killing " + str(containers_to_kill) + e
                        )
                        if os.environ.get("LOG_LEVEL", "info").lower() == "debug":
                            logger.exception(e)
                if kind == "program":
                    self.program_exit_code = return_code
                    self.program_elapsed_time = elapsed_time
                elif kind == "ingestion":
                    self.ingestion_program_exit_code = return_code
                    self.ingestion_elapsed_time = elapsed_time
                logger.info(f"[exited with {logs['returncode']}]")
                for key, value in logs.items():
                    if key not in ["stdout", "stderr"]:
                        continue
                    if value["data"]:
                        logger.info(f"[{key}]\n{value['data']}")
                        self._put_file(value["location"], raw_data=value["data"])

                # set logs of this kind to None, since we handled them already
                logger.info("Program finished")
        signal.alarm(0)

        if self.is_scoring:
            self._update_status(STATUS_FINISHED)
        else:
            self._update_status(STATUS_SCORING)

    def push_scores(self):
        """This is only ran at the end of the scoring step"""
        # POST to some endpoint:
        # {
        #     "correct": 1.0
        # }
        if os.path.exists(os.path.join(self.output_dir, "scores.json")):
            scores_file = os.path.join(self.output_dir, "scores.json")
            with open(scores_file) as f:
                try:
                    scores = json.load(f)
                except json.decoder.JSONDecodeError as e:
                    raise SubmissionException(
                        f"Could not decode scores json properly, it contains an error.\n{e.msg}"
                    )

        elif os.path.exists(os.path.join(self.output_dir, "scores.txt")):
            scores_file = os.path.join(self.output_dir, "scores.txt")
            with open(scores_file) as f:
                scores = yaml.load(f, yaml.Loader)
        else:
            raise SubmissionException(
                "Could not find scores file, did the scoring program output it?"
            )

        url = (
            f"{self.submissions_api_url}/upload_submission_scores/{self.submission_id}/"
        )
        data = {
            "secret": self.secret,
            "scores": scores,
        }
        logger.info(f"Submitting these scores to {url}: {scores} with data = {data}")
        resp = self.requests_session.post(url, json=data)
        logger.info(resp)
        logger.info(str(resp.content))

    def push_output(self):
        """Output is pushed at the end of both prediction and scoring steps."""
        # V1.5 compatibility, write program statuses to metadata file
        prog_status = {
            "exitCode": self.program_exit_code,
            # for v1.5 compat, send `ingestion_elapsed_time` if no `program_elapsed_time`
            "elapsedTime": self.program_elapsed_time or self.ingestion_elapsed_time,
            "ingestionExitCode": self.ingestion_program_exit_code,
            "ingestionElapsedTime": self.ingestion_elapsed_time,
        }

        logger.info(f"Metadata output: {prog_status}")

        metadata_path = os.path.join(self.output_dir, "metadata")

        if os.path.exists(metadata_path):
            raise SubmissionException(
                "Error, the output directory already contains a metadata file. This file is used "
                "to store exitCode and other data, do not write to this file manually."
            )

        with open(metadata_path, "w") as f:
            f.write(yaml.dump(prog_status, default_flow_style=False))

        if not self.is_scoring:
            self._put_dir(self.prediction_result, self.output_dir)
        else:
            self._put_dir(self.scoring_result, self.output_dir)

    def clean_up(self):
        if os.environ.get("CODALAB_IGNORE_CLEANUP_STEP"):
            logger.warning(
                f"CODALAB_IGNORE_CLEANUP_STEP mode enabled, ignoring clean up of: {self.root_dir}"
            )
            return

        logger.info(f"Destroying submission temp dir: {self.root_dir}")
        shutil.rmtree(self.root_dir)

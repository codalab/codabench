import time

import json
import shutil
import uuid
import websockets

import asyncio
import glob
import logging
import os

import requests
import tempfile
import yaml
import zipfile
from billiard.exceptions import SoftTimeLimitExceeded
from celery import Celery, task
from shutil import make_archive
from subprocess import CalledProcessError, check_output
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlretrieve
from zipfile import ZipFile

app = Celery()
app.config_from_object('celery_config')  # grabs celery_config.py

logger = logging.getLogger()


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


class SubmissionException(Exception):
    pass


@task(name="compute_worker_run")
def run_wrapper(run_args):
    logger.info(f"Received run arguments: {run_args}")
    run = Run(run_args)

    try:
        run.prepare()
        run.start()
        if run.is_scoring:
            run.push_scores()
            # TODO: Also output push result at some point, so SCORING STEPS have output as well?
            #   run.push_result()
            #   when this is changed, make sure to include files in submission manager download section
        else:
            run.push_result()
    except SubmissionException as e:
        run._update_status(STATUS_FAILED, str(e))
    except SoftTimeLimitExceeded:
        run._update_status(STATUS_FAILED, "Soft time limit exceeded!")
    finally:
        run.clean_up()


class Run:
    """A "Run" in Codalab is composed of some program, some data to work with, and some signed URLs to upload results
    to.  Currently, the run_args are:



    """

    def __init__(self, run_args):
        # Directories for the run
        self.root_dir = tempfile.mkdtemp(dir="/tmp/codalab-v2")
        self.output_dir = os.path.join(self.root_dir, "output")

        # Details for submission
        self.is_scoring = run_args["is_scoring"]
        self.submission_id = run_args["id"]
        self.api_url = run_args["api_url"]
        self.docker_image = run_args["docker_image"]
        self.secret = run_args["secret"]
        self.result = run_args["result"]  # TODO, rename this to result_url
        self.execution_time_limit = run_args["execution_time_limit"]
        # stdout and stderr
        self.stdout, self.stderr, self.ingestion_stdout, self.ingestion_stderr = self._get_stdout_stderr_file_names(run_args)

        self.program_data = run_args.get("program_data", None)
        self.ingestion_program_data = run_args.get("ingestion_program", None)
        self.input_data = run_args.get("input_data", None)
        self.reference_data = run_args.get("reference_data", None)

        self.task_pk = run_args.get('task_pk')
        self.parent_pk = run_args.get('parent_pk')
        self.parent_secret = run_args.get('parent_secret')

        # Socket connection to stream output of submission
        api_url_parsed = urlparse(self.api_url)
        websocket_host = api_url_parsed.netloc
        websocket_scheme = 'ws' if api_url_parsed.scheme == 'http' else 'wss'
        self.websocket_url = f"{websocket_scheme}://{websocket_host}/"

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

    def _update_status(self, status, extra_information=None):
        if status not in AVAILABLE_STATUSES:
            raise SubmissionException(f"Status '{status}' is not in available statuses: {AVAILABLE_STATUSES}")
        url = f"{self.api_url}/submissions/{self.submission_id}/"
        logger.info(f"Updating status to '{status}' with extra_information = '{extra_information}' for submission = {self.submission_id}")
        data = {
            "secret": self.secret,
            "status": status,
            "status_details": extra_information,
        }
        if status == STATUS_SCORING:
            data.update({
                "task_pk": self.task_pk,
                "parent_pk": self.parent_pk,
                "parent_secret": self.parent_secret,
            })
        resp = requests.patch(url, data)
        # logger.info(resp)
        # logger.info(resp.content)

    def _get_docker_image(self, image_name):
        logger.info("Running docker pull for image: {}".format(image_name))
        try:
            cmd = ['docker', 'pull', image_name]
            docker_pull = check_output(cmd)
            logger.info("Docker pull complete for image: {0} with output of {1}".format(image_name, docker_pull))
        except CalledProcessError:
            logger.info("Docker pull for image: {} returned a non-zero exit code!")
            raise SubmissionException(f"Docker pull for {image_name} failed!")

    def _get_bundle(self, url, destination):
        logger.info(f"Getting bundle {url} to unpack @{destination}")
        bundle_file = tempfile.NamedTemporaryFile()

        try:
            urlretrieve(url, bundle_file.name)
        except HTTPError:
            raise SubmissionException(f"Problem fetching {url} to put in {destination}")

        with ZipFile(bundle_file.file, 'r') as z:
            z.extractall(os.path.join(self.root_dir, destination))

    async def _run_docker_cmd(self, docker_cmd, kind):
        """This runs a command and asynchronously writes the data to both a storage file
        and a socket"""
        url = f'{self.websocket_url}submission_input/{self.submission_id}/'
        logger.info(f"Connecting to {url}")


        # We should send headers with the secret.
        #     * ``extra_headers`` sets additional HTTP request headers – it can be a
        #       :class:`~websockets.http.Headers` instance, a
        #       :class:`~collections.abc.Mapping`, or an iterable of ``(name, value)``
        #       pairs

        async with websockets.connect(url) as websocket:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            logs = {
                "stdout": {
                    "data": b'',
                    "stream": proc.stdout,
                    "continue": True,
                    "location": self.stdout if kind == 'program' else self.ingestion_stdout
                },
                "stderr": {
                    "data": b'',
                    "stream": proc.stderr,
                    "continue": True,
                    "location": self.stderr if kind == 'program' else self.ingestion_stderr
                },
            }

            while any(v["continue"] for v in logs.values()):
                for value in logs.values():
                    out = await value["stream"].readline()
                    if out:
                        value["data"] += out
                        print("DATA!!!! " + str(out))
                        await websocket.send(out.decode())
                    else:
                        value["continue"] = False

            logger.info(f'[exited with {proc.returncode}]')
            for key, value in logs.items():
                if value["data"]:
                    logger.info(f'[{key}]\n{value["data"]}')
                    self._put_file(value["location"], raw_data=value["data"])

    def _run_program_directory(self, program_dir, kind, can_be_output=False):
        # TODO: read Docker image from metadatas??? ** do it in prepare??? **

        # If the directory doesn't even exist, move on
        if not os.path.exists(program_dir):
            logger.info(f"{program_dir} not found, no program to execute")
            return

        try:
            with open(os.path.join(program_dir, "metadata.yaml"), 'r') as metadata_file:
                metadata = yaml.load(metadata_file.read())
                command = metadata.get("command")
                if not command:
                    raise SubmissionException("Program directory missing 'command' in metadata")
        except FileNotFoundError:
            if can_be_output:
                logger.info("Program directory missing 'metadata.yaml', assuming it's going to be handled by ingestion "
                            "program so move it to output")
                shutil.move(program_dir, self.output_dir)
                return
            else:
                raise SubmissionException("Program directory missing 'metadata.yaml'")

        docker_cmd = [
            'docker',
            'run',
            # Remove it after run
            '--rm',
            # Try the new timeout feature
            '--stop-timeout={}'.format(self.execution_time_limit),
            # Don't allow subprocesses to raise privileges
            '--security-opt=no-new-privileges',
            # Set the right volume
            '-v', f'{program_dir}:/app',
            '-v', f'{self.output_dir}:/app/output',
            # Start in the right directory
            '-w', '/app',
            # Don't buffer python output, so we don't lose any
            '-e', 'PYTHONUNBUFFERED=1',
        ]

        # TODO: Should pass in reference data if scoring, or something?

        # TODO: Check with zhengying (already contacted him, waiting) on whether we need a hidden dir or not.
        if kind == 'ingestion' and self.input_data:
            docker_cmd += ['-v', f'{os.path.join(self.root_dir, "input_data")}:/app/hidden']

        if self.is_scoring:
            # For scoring programs, we want to have a shared directory just in case we have an ingestion program.
            # This will add the share dir regardless of ingestion or scoring, as long as we're `is_scoring`
            docker_cmd += ['-v', f'{os.path.join(self.root_dir, "shared")}:/app/shared']

        # Set the image name (i.e. "codalab/codalab-legacy") for the container
        docker_cmd += [self.docker_image]

        # Append the actual program to run
        docker_cmd += command.split(' ')

        logger.info(f"Running program = {' '.join(docker_cmd)}")

        # This runs the docker command and asychronously passes data
        asyncio.get_event_loop().run_until_complete(self._run_docker_cmd(docker_cmd, kind=kind))

        logger.info(f"Program finished")

    def _put_dir(self, url, directory):
        logger.info("Putting dir %s in %s" % (directory, url))

        zip_path = make_archive(os.path.join(self.root_dir, str(uuid.uuid4())), 'zip', directory)
        self._put_file(url, file=zip_path)

    def _put_file(self, url, file=None, raw_data=None):

        if file and raw_data:
            raise Exception("Cannot put both a file and raw_data")

        headers = {
            'Content-Type': 'application/zip',

            # For Azure only, should turn on/off based on storage...
            'x-ms-blob-type': 'BlockBlob',
            'x-ms-version': '2018-03-28',
        }

        if file:
            logger.info("Putting file %s in %s" % (file, url))
            data = open(file, 'rb')
            headers['Content-Length'] = str(os.path.getsize(file))
        elif raw_data:
            logger.info("Putting raw data %s in %s" % (raw_data, url))
            data = raw_data
        else:
            raise SubmissionException('Must provide data, both file and raw_data cannot be empty')

        resp = requests.put(
            url,
            data=data,
            headers=headers,
        )
        logger.info("*** PUT RESPONSE: ***")
        logger.info(f'response: {resp}')
        logger.info(f'content: {resp.content}')

    def prepare(self):
        self._update_status(STATUS_PREPARING)

        # A run *may* contain the following bundles, let's grab them and dump them in the appropriate
        # sub folder.
        bundles = [
            # (url to file, relative folder destination)
            (self.program_data, 'program'),
            (self.ingestion_program_data, 'ingestion_program'),
            (self.input_data, 'input_data'),
            (self.reference_data, 'reference_data'),
        ]

        if self.is_scoring:
            # Send along submission result so scoring_program can get access
            bundles += [(self.result, os.path.join('program', 'input'))]

        for url, path in bundles:
            if url is not None:
                self._get_bundle(url, path)

        # For logging purposes let's dump file names
        for filename in glob.iglob(self.root_dir + '**/*.*', recursive=True):
            logger.info(filename)

        # Before the run starts we want to download docker images, they may take a while to download
        # and to do this during the run would subtract from the participants time.
        self._get_docker_image(self.docker_image)

    def start(self):
        if not self.is_scoring:
            self._update_status(STATUS_RUNNING)

        program_dir = os.path.join(self.root_dir, "program")
        ingestion_program_dir = os.path.join(self.root_dir, "ingestion_program")

        self._run_program_directory(program_dir, kind='program', can_be_output=True)
        self._run_program_directory(ingestion_program_dir, kind='ingestion')

        # Unpack submission and data into some directory
        # Download docker image
        # ** When running SCORING PROGRAM ** pass by volume the codalab.py library file so submissions/organizers can use it
        # Normal things pass all run_args as env vars to submission
        # Upload submission results
        # Upload submission stdout/etc.

        if self.is_scoring:
            self._update_status(STATUS_FINISHED)
        else:
            self._update_status(STATUS_SCORING)

    def push_scores(self):
        # POST to some endpoint:
        # {
        #     "correct": 1.0
        # }
        try:
            scores_file = os.path.join(self.output_dir, "scores.json")
            scores = json.load(open(scores_file, 'r'))
        except FileNotFoundError:
            raise SubmissionException("Could not find scores.json, did the scoring program output it?")

        url = f"{self.api_url}/upload_submission_scores/{self.submission_id}/"
        logger.info(f"Submitting these scores to {url}: {scores}")
        resp = requests.post(url, json={
            "secret": self.secret,
            "scores": scores,
        })
        logger.info(resp)
        logger.info(str(resp.content))

    def push_result(self):
        self._put_dir(self.result, self.output_dir)

    def clean_up(self):
        logger.info("We're not cleaning up yet... TODO: cleanup!")
        pass

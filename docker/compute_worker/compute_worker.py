import time
import websockets

import asyncio
import glob
import logging
import os

import requests
import subprocess
import tempfile
from billiard.exceptions import SoftTimeLimitExceeded
from celery import Celery, task
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
STATUS_FINISHED = "Finished"
STATUS_FAILED = "Failed"
AVAILABLE_STATUSES = (
    STATUS_NONE,
    STATUS_SUBMITTING,
    STATUS_SUBMITTED,
    STATUS_PREPARING,
    STATUS_RUNNING,
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
    except SubmissionException as e:
        run.update_status(STATUS_FAILED, str(e))
    except SoftTimeLimitExceeded:
        run.update_status(STATUS_FAILED, "Soft time limit exceeded!")



# class Logger(object):
#     def __init__(self, output_file, output_url):
#         # self.output_file = open("logfile.log", "a")
#         self.output_socket
#
#     def write(self, message):
#         # self.output_file.write(message)
#
#     def flush(self):
#         # this flush method is needed for python 3 compatibility.
#         # this handles the flush command by doing nothing.
#         # you might want to specify some extra behavior here.
#         pass



class Run:
    def __init__(self, run_args):
        self.root_dir = tempfile.mkdtemp(dir="/tmp/codalab-v2")
        self.submission_id = run_args["id"]
        self.api_url = run_args["api_url"]
        self.docker_image = run_args["docker_image"]
        self.secret = run_args["secret"]
        self.execution_time_limit = run_args["execution_time_limit"]

        self.submission_data = run_args.get("submission_data", None)
        self.input_data = run_args.get("input_data", None)
        self.reference_data = run_args.get("reference_data", None)

        api_url_parsed = urlparse(self.api_url)
        websocket_host = api_url_parsed.netloc
        websocket_scheme = 'ws' if api_url_parsed.scheme == 'http' else 'wss'
        self.websocket_url = f"{websocket_scheme}://{websocket_host}/"

    def update_status(self, status, extra_information=None):
        if status not in AVAILABLE_STATUSES:
            raise SubmissionException(f"Status '{status}' is not in available statuses: {AVAILABLE_STATUSES}")
        url = f"{self.api_url}/submissions/{self.submission_id}/"
        logger.info(f"Status = '{status}' with extra_information = '{extra_information}' for submission = {self.submission_id}")
        resp = requests.patch(url, {
            "secret": self.secret,
            "status": status,
            "status_details": extra_information,
        })
        # print(resp)
        # print(resp.content)

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
            raise SubmissionException(f"Problem fetching {destination}")

        with ZipFile(bundle_file.file, 'r') as z:
            z.extractall(os.path.join(self.root_dir, destination))

    def _dump_files(self):
        for filename in glob.iglob(self.root_dir + '**/*.*', recursive=True):
            print(filename)

    def prepare(self):
        self.update_status(STATUS_PREPARING)

        bundles = (
            # (url to file, relative folder destination)
            (self.submission_data, 'submission'),
            (self.input_data, 'input_data'),
            (self.reference_data, 'reference_data'),
        )

        for url, path in bundles:
            self._dump_files()
            if url is not None:
                self._get_bundle(url, path)

        self._dump_files()

        self._get_docker_image(self.docker_image)

    def start(self):
        self.update_status(STATUS_RUNNING)
        print("We hit this! Now sleeping...")

        stdout_file = os.path.join(self.root_dir, "stdout.txt")
        stderr_file = os.path.join(self.root_dir, "stderr.txt")
        stdout = open(stdout_file, "a+")
        stderr = open(stderr_file, "a+")

        docker_cmd = (
            'docker',
            'run',
            # Remove it after run
            '--rm',
            # Try the new timeout feature
            '--stop-timeout={}'.format(self.execution_time_limit),
            # Don't allow subprocesses to raise privileges
            '--security-opt=no-new-privileges',
            # Set the right volume
            '-v', '{0}:/app'.format(self.root_dir),
            # Start in the right directory
            '-w', '/app',
            # Don't buffer python output, so we don't lose any
            '-e', 'PYTHONUNBUFFERED=1',
            # Note that hidden data dir is excluded here!
            # Set the right image
            self.docker_image,

            'python', 'submission/submission.py',
        )

        logger.info(f"Running program = {' '.join(docker_cmd)}")

        exit_code = None

        # asyncio.get_event_loop().run_until_complete(
        #     self._run_cmd(docker_cmd)
        # )

        asyncio.get_event_loop().run_until_complete(self._run_cmd(docker_cmd))


        logger.info(f"Program finished with exit code = {exit_code}")

        # Unpack submission and data into some directory
        # Download docker image
        # ** When running SCORING PROGRAM ** pass by volume the codalab.py library file so submissions/organizers can use it
        # Normal things pass all run_args as env vars to submission
        # Upload submission results
        # Upload submission stdout/etc.

        self.update_status(STATUS_FINISHED)

    async def _run_cmd(self, docker_cmd):
        logger.info(f"Connecting to {self.websocket_url}submission_input/")
        async with websockets.connect(f'{self.websocket_url}submission_input/') as websocket:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            while True:
                data = await proc.stdout.readline()
                if data:
                    print("DATA!!!! " + str(data))
                    await websocket.send(data.decode())
                else:
                    break


            stdout, stderr = await proc.communicate()

            print(f'[exited with {proc.returncode}]')
            if stdout:
                print(f'[stdout]\n{stdout.decode()}')
            if stderr:
                print(f'[stderr]\n{stderr.decode()}')

            # for _ in range(10):
            #     time.sleep(1)
            #     print("Sending hello world stuff")
            #

            # process = subprocess.Popen(docker_cmd, stdout=stdout, stderr=stderr)
            #
            # # While either program is running and hasn't exited, continue polling
            # while (process and exit_code == None):
            #     time.sleep(1)
            #
            #     if process and exit_code is None:
            #         exit_code = process.poll()




# class SocketEchoStreamReader(asyncio.StreamReader):
#     async def



# def _update_status(run_args, status):
#     submission_id = run_args["id"]
#     api_url = run_args["api_url"]
#     secret = run_args["secret"]
#     url = f"{api_url}/submissions/{submission_id}/"
#     print(f"Sending '{status}' update for submission={submission_id}")
#     resp = requests.patch(url, {"secret": secret, "status": status})
#     print(resp)
#     print(resp.content)
#
#
# def run(run_args):
#     print("We hit this!")
#     print(run_args)
#     _update_status(run_args, STATUS_RUNNING)












    pass


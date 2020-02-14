import asyncio
import glob
import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from shutil import make_archive
from subprocess import CalledProcessError, check_output
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlretrieve
from zipfile import ZipFile

import requests
import websockets
import yaml
from billiard.exceptions import SoftTimeLimitExceeded
from celery import Celery, task

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
        run.push_output()
    except SubmissionException as e:
        run._update_status(STATUS_FAILED, str(e))
    except SoftTimeLimitExceeded:
        run._update_status(STATUS_FAILED, "Soft time limit exceeded!")
    finally:
        run.clean_up()


def replace_legacy_metadata_command(command, kind, is_scoring, ingestion_only_during_scoring=False):
    vars_to_replace = [
        ('$input', '/app/input_data' if kind == 'ingestion' else '/app/input'),
        ('$output', '/app/output'),
        ('$program', '/app/ingestion_program' if ingestion_only_during_scoring and is_scoring else '/app/program'),
        ('$ingestion_program', '/app/program'),
        ('$hidden', '/app/input/ref'),
        ('$shared', '/app/shared'),
        ('$submission_program', '/app/ingested_program'),
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


class Run:
    """A "Run" in Codalab is composed of some program, some data to work with, and some signed URLs to upload results
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
        self.root_dir = tempfile.mkdtemp(dir="/tmp/codalab-v2")
        self.input_dir = os.path.join(self.root_dir, "input")
        self.output_dir = os.path.join(self.root_dir, "output")

        # Details for submission
        self.is_scoring = run_args["is_scoring"]
        self.user_pk = run_args["user_pk"]
        self.submission_id = run_args["id"]
        self.submissions_api_url = run_args["submissions_api_url"]
        self.docker_image = run_args["docker_image"]
        self.secret = run_args["secret"]
        self.prediction_result = run_args["prediction_result"]
        self.scoring_result = run_args.get("scoring_result")
        self.execution_time_limit = run_args["execution_time_limit"]
        # stdout and stderr
        self.stdout, self.stderr, self.ingestion_stdout, self.ingestion_stderr = self._get_stdout_stderr_file_names(run_args)

        self.program_data = run_args.get("program_data")
        self.ingestion_program_data = run_args.get("ingestion_program")
        self.input_data = run_args.get("input_data")
        self.reference_data = run_args.get("reference_data")
        self.ingestion_only_during_scoring = run_args.get('ingestion_only_during_scoring')
        self.detailed_results_url = run_args.get('detailed_results_url')
        self.watcher = None

        self.task_pk = run_args.get('task_pk')

        # During prediction program will be the submission program, during scoring it will be the
        # scoring program
        self.program_exit_code = None
        self.ingestion_program_exit_code = None

        self.program_elapsed_time = None
        self.ingestion_elapsed_time = None

        # Socket connection to stream output of submission
        submission_api_url_parsed = urlparse(self.submissions_api_url)
        websocket_host = submission_api_url_parsed.netloc
        websocket_scheme = 'ws' if submission_api_url_parsed.scheme == 'http' else 'wss'
        self.websocket_url = f"{websocket_scheme}://{websocket_host}/submission_input/{self.user_pk}/{self.submission_id}/{self.secret}/"

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

        resp = requests.patch(url, data)
        if resp.status_code != 200:
            logger.info(f"Submission patch failed with status = {resp.status_code}, and response = \n{resp.content}")
            raise SubmissionException("Failure updating submission data.")

    def _update_status(self, status, extra_information=None):
        if status not in AVAILABLE_STATUSES:
            raise SubmissionException(f"Status '{status}' is not in available statuses: {AVAILABLE_STATUSES}")
        logger.info(
            f"Updating status to '{status}' with extra_information = '{extra_information}' "
            f"for submission = {self.submission_id}"
        )
        data = {
            "status": status,
            "status_details": extra_information,
        }
        if status == STATUS_SCORING:
            data.update({
                "task_pk": self.task_pk,
            })
        self._update_submission(data)

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
        """Downloads zip from url and unpacks it into destination

        :returns zip file path"""
        logger.info(f"Getting bundle {url} to unpack @{destination}")
        bundle_file = tempfile.NamedTemporaryFile(delete=False)

        try:
            urlretrieve(url, bundle_file.name)
        except HTTPError:
            raise SubmissionException(f"Problem fetching {url} to put in {destination}")

        with ZipFile(bundle_file.file, 'r') as z:
            z.extractall(os.path.join(self.root_dir, destination))
        return bundle_file.name

    async def _run_docker_cmd(self, docker_cmd, kind):
        """This runs a command and asynchronously writes the data to both a storage file
        and a socket

        :param docker_cmd: the list of docker command arguments
        :param kind: either 'ingestion' or 'program'
        :return:
        """
        logger.info(f"Connecting to {self.websocket_url}")

        async with websockets.connect(self.websocket_url) as websocket:
            start = time.time()
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
                    try:
                        out = await asyncio.wait_for(value["stream"].readline(), timeout=.1)
                        if out:
                            value["data"] += out
                            print("WS: " + str(out))
                            await websocket.send(json.dumps({
                                "kind": kind,
                                "message": out.decode()
                            }))
                        else:
                            value["continue"] = False
                    except asyncio.TimeoutError:
                        continue

            end = time.time()

            if kind == 'program':
                self.program_exit_code = proc.returncode
                self.program_elapsed_time = end - start
                if self.watcher:
                    self.watcher.terminate()
            elif kind == 'ingestion':
                self.ingestion_program_exit_code = proc.returncode
                self.ingestion_elapsed_time = end - start

            logger.info(f'[exited with {proc.returncode}]')
            for key, value in logs.items():
                if value["data"]:
                    logger.info(f'[{key}]\n{value["data"]}')
                    self._put_file(value["location"], raw_data=value["data"])

            logger.info("Program finished")
            return proc

    async def _run_program_directory(self, program_dir, kind, can_be_output=False):
        # If the directory doesn't even exist, move on
        if not os.path.exists(program_dir):
            logger.info(f"{program_dir} not found, no program to execute")
            return

        if os.path.exists(os.path.join(program_dir, "metadata.yaml")):
            metadata_path = 'metadata.yaml'
        elif os.path.exists(os.path.join(program_dir, "metadata")):
            metadata_path = 'metadata'
        else:
            if can_be_output:
                logger.info(
                    "Program directory missing metadata, assuming it's going to be handled by ingestion "
                    "program so move it to output"
                )
                # Copying so that we don't move a code submission w/out a metadata command
                shutil.copytree(program_dir, self.output_dir)
                return
            else:
                raise SubmissionException("Program directory missing 'metadata.yaml/metadata'")

        logger.info(f"Metadata path is {os.path.join(program_dir, metadata_path)}")
        with open(os.path.join(program_dir, metadata_path), 'r') as metadata_file:
            metadata = yaml.load(metadata_file.read(), Loader=yaml.FullLoader)
            logger.info(f"Metadata contains:\n {metadata}")
            command = metadata.get("command")
            if not command and kind == "ingestion":
                raise SubmissionException("Program directory missing 'command' in metadata")
            elif not command:
                logger.info(
                    f"Warning: {program_dir} has no command in metadata, continuing anyway "
                    f"(may be meant to be consumed by an ingestion program)"
                )
                return

        docker_cmd = [
            'docker',
            'run',
            # Remove it after run
            '--rm',

            # Try the new timeout feature
            '--stop-timeout={}'.format(self.execution_time_limit),

            # Don't allow subprocesses to raise privileges
            '--security-opt=no-new-privileges',

            # Set the volumes
            '-v', f'{program_dir}:/app/program',
            '-v', f'{self.output_dir}:/app/output',

            # Start in the right directory
            '-w', '/app/program',

            # Don't buffer python output, so we don't lose any
            '-e', 'PYTHONUNBUFFERED=1',
        ]

        if kind == 'ingestion':
            # program here is either scoring program or submission, depends on if this ran during Prediction or Scoring
            if self.ingestion_only_during_scoring and self.is_scoring:
                # submission program moved to 'input/res' with shutil.move() above
                ingested_program_location = "input/res"
            else:
                ingested_program_location = "program"

            docker_cmd += ['-v', f'{os.path.join(self.root_dir, ingested_program_location)}:/app/ingested_program']

        if self.input_data:
            docker_cmd += ['-v', f'{os.path.join(self.root_dir, "input_data")}:/app/input_data']

        if self.is_scoring:
            # For scoring programs, we want to have a shared directory just in case we have an ingestion program.
            # This will add the share dir regardless of ingestion or scoring, as long as we're `is_scoring`
            docker_cmd += ['-v', f'{os.path.join(self.root_dir, "shared")}:/app/shared']

            # Input from submission (or submission + ingestion combo)
            docker_cmd += ['-v', f'{self.input_dir}:/app/input']
            if self.detailed_results_url and self.is_scoring and kind == 'program':
                # we have a detailed results url, we are in the scoring step, and we aren't the ingestion program
                detail_path = os.path.join(self.output_dir, "detailed_results.html")

                # Is there a better way to create the entire path without having to mkdir each incremental step?
                if not os.path.exists(detail_path):
                    if not os.path.exists(self.output_dir):
                        os.mkdir(self.output_dir)
                    open(detail_path, 'a').close()

                    # Change perms so we can read the file to send to the sas URL
                    os.chmod(detail_path, 0o777)

                _command = ['./watch.sh', self.detailed_results_url, detail_path, self.websocket_url, self.output_dir]
                self.watcher = subprocess.Popen(_command, stderr=subprocess.STDOUT)

        # Set the image name (i.e. "codalab/codalab-legacy") for the container
        docker_cmd += [self.docker_image]

        # Handle Legacy competitions by replacing anything in the run command
        command = replace_legacy_metadata_command(
            command=command,
            kind=kind,
            is_scoring=self.is_scoring,
            ingestion_only_during_scoring=self.ingestion_only_during_scoring
        )

        # Append the actual program to run
        docker_cmd += command.split(' ')

        logger.info(f"Running program = {' '.join(docker_cmd)}")

        # This runs the docker command and asynchronously passes data back via websocket
        return await self._run_docker_cmd(docker_cmd, kind=kind)

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
            (self.reference_data, 'input/ref'),
        ]

        if self.is_scoring:
            # Send along submission result so scoring_program can get access
            bundles += [(self.prediction_result, 'input/res')]

        for url, path in bundles:
            if url is not None:
                zip_file = self._get_bundle(url, path)

                # TODO: When we have `is_scoring_only` this needs to change...
                if url == self.program_data and not self.is_scoring:
                    # We want to get a checksum of submissions so we can check if they are
                    # a solution, or maybe match them against other submissions later
                    logger.info(f"Beginning MD5 checksum of submission: {zip_file}")
                    checksum = md5(zip_file)
                    logger.info(f"Checksum result: {checksum}")
                    self._update_submission({"md5": checksum})

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

        logger.info("Running scoring program, and then ingestion program")

        loop = asyncio.new_event_loop()

        gathered_tasks = asyncio.gather(
            self._run_program_directory(program_dir, kind='program', can_be_output=True),
            self._run_program_directory(ingestion_program_dir, kind='ingestion'),
            loop=loop,
        )
        loop.run_until_complete(gathered_tasks)

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
                    raise SubmissionException(f"Could not decode scores json properly, it contains an error.\n{e.msg}")

        elif os.path.exists(os.path.join(self.output_dir, "scores.txt")):
            scores_file = os.path.join(self.output_dir, "scores.txt")
            with open(scores_file) as f:
                scores = yaml.load(f)

        else:
            raise SubmissionException("Could not find scores file, did the scoring program output it?")

        url = f"{self.submissions_api_url}/upload_submission_scores/{self.submission_id}/"
        logger.info(f"Submitting these scores to {url}: {scores}")
        resp = requests.post(url, json={
            "secret": self.secret,
            "scores": scores,
        })
        logger.info(resp)
        logger.info(str(resp.content))

    def push_output(self):
        """Output is pushed at the end of both prediction and scoring steps."""
        # V1.5 compatibility, write program statuses to metadata file
        prog_status = {
            'exitCode': self.program_exit_code,
            # for v1.5 compat, send `ingestion_elapsed_time` if no `program_elapsed_time`
            'elapsedTime': self.program_elapsed_time or self.ingestion_elapsed_time,
            'ingestionExitCode': self.ingestion_program_exit_code,
            'ingestionElapsedTime': self.ingestion_elapsed_time,
        }

        logger.info(f"Metadata output: {prog_status}")

        metadata_path = os.path.join(self.output_dir, 'metadata')

        if os.path.exists(metadata_path):
            raise SubmissionException("Error, the output directory already contains a metadata file. This file is used "
                                      "to store exitCode and other data, do not write to this file manually.")

        with open(metadata_path, 'w') as f:
            f.write(yaml.dump(prog_status, default_flow_style=False))

        if not self.is_scoring:
            self._put_dir(self.prediction_result, self.output_dir)
        else:
            self._put_dir(self.scoring_result, self.output_dir)

    def clean_up(self):
        logger.info("We're not cleaning up yet... TODO: cleanup!")
        pass

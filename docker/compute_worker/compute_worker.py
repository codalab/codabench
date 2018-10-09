import logging
import os

import requests
from billiard.exceptions import SoftTimeLimitExceeded
from celery import Celery, task
from subprocess import CalledProcessError, check_output

app = Celery()
app.config_from_object('celery_config')  # grabs celery_config.py

logger = logging.getLogger()


# Status options for submissions
STATUS_NONE = "None"
STATUS_SUBMITTING = "Submitting"
STATUS_SUBMITTED = "Submitted"
STATUS_RUNNING = "Running"
STATUS_FINISHED = "Finished"
STATUS_FAILED = "Failed"
AVAILABLE_STATUSES = (
    STATUS_NONE,
    STATUS_SUBMITTING,
    STATUS_SUBMITTED,
    STATUS_RUNNING,
    STATUS_FINISHED,
    STATUS_FAILED,
)


class SubmissionException(Exception):
    pass


@task(name="compute_worker_run")
def run_wrapper(run_args):
    run = Run(run_args)

    try:
        run.start()
    except SubmissionException as e:
        run.update_status(STATUS_FAILED, str(e))
    except SoftTimeLimitExceeded:
        run.update_status(STATUS_FAILED, "Soft time limit exceeded!")


class Run:
    def __init__(self, run_args):
        self.submission_id = run_args["id"]
        self.api_url = run_args["api_url"]
        self.docker_image = run_args["docker_image"]
        self.secret = run_args["secret"]

    def update_status(self, status, extra_information=None):
        if status not in AVAILABLE_STATUSES:
            raise SubmissionException(f"Status '{status}' is not in available statuses: {AVAILABLE_STATUSES}")
        url = f"{self.api_url}/submissions/{self.submission_id}/"
        print(f"Sending '{status}' update for submission={self.submission_id}")
        resp = requests.patch(url, {
            "secret": self.secret,
            "status": status,
            "status_details": extra_information,
        })
        print(resp)
        print(resp.content)

    def get_docker_image(self, image_name):
        logger.info("Running docker pull for image: {}".format(image_name))
        try:
            cmd = ['docker', 'pull', image_name]
            docker_pull = check_output(cmd)
            logger.info("Docker pull complete for image: {0} with output of {1}".format(image_name, docker_pull))
        except CalledProcessError:
            logger.info("Docker pull for image: {} returned a non-zero exit code!")
            raise SubmissionException(f"Docker pull for {image_name} failed!")

    def start(self):
        print("We hit this! Now sleeping...")
        self.update_status(STATUS_RUNNING)

        self.get_docker_image(self.docker_image)





        # Unpack submission and data into some directory
        # Download docker image
        # ** When running SCORING PROGRAM ** pass by volume the codalab.py library file so submissions/organizers can use it
        # Normal things pass all run_args as env vars to submission
        # Upload submission results
        # Upload submission stdout/etc.














        for _ in range(100):
            import time; time.sleep(1)
            print("Slept for a second...")

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


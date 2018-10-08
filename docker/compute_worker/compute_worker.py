import os

import requests
from billiard.exceptions import SoftTimeLimitExceeded
from celery import Celery, task


app = Celery()
app.config_from_object('celery_config')  # grabs celery_config.py


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


@task(name="compute_worker_run")
def run_wrapper(run_args):
    run = Run(run_args)

    try:
        run.start()
    except SoftTimeLimitExceeded:
        run.update_status(STATUS_FAILED)


class Run:
    def __init__(self, run_args):
        self.submission_id = run_args["id"]
        self.api_url = run_args["api_url"]
        self.secret = run_args["secret"]

    def update_status(self, status):
        if status not in AVAILABLE_STATUSES:
            raise Exception(f"Status '{status}' is not in available statuses: {AVAILABLE_STATUSES}")
        url = f"{self.api_url}/submissions/{self.submission_id}/"
        print(f"Sending '{status}' update for submission={self.submission_id}")
        resp = requests.patch(url, {"secret": self.secret, "status": status})
        print(resp)
        print(resp.content)

    def start(self):
        print("We hit this! Now sleeping...")
        self.update_status(STATUS_RUNNING)

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


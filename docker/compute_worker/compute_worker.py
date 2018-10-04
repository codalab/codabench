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


@task(name="compute_worker_run")
def run_wrapper(run_args):
    try:
        run(run_args)
    except SoftTimeLimitExceeded:
        _update_status(run_args, STATUS_FAILED)


def _update_status(run_args, status):
    submission_id = run_args["id"]
    api_url = run_args["api_url"]
    secret = run_args["secret"]
    url = f"{api_url}/submissions/{submission_id}/"
    print(f"Sending '{status}' update for submission={submission_id}")
    resp = requests.patch(url, {"secret": secret, "status": status})
    print(resp)
    print(resp.content)


def run(run_args):
    print("We hit this!")
    print(run_args)
    _update_status(run_args, STATUS_RUNNING)
    pass


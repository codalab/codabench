#!/usr/bin/env python3
"""
Overview
========
    This script is built to guide a user through the selection of both a submission id and a task id.
    These ids are used to demonstrate the ability of a robot user to re-run a submission on a specific
    task. This can be used to enable clinicians to run pre-built algorithms on private datasets that
    are not attached to any competition.


Usage
=====
    To re-run a submission on a task, this script can be run with arguments of a submission id and a
    task id as shown below:

    ./rerun_submission.py <int:submission_id> <uuid:task_key>

    The following instruction list will provide a detailed guide in selecting a submission and task id.


1. Create a competition that allows robots, and create a user marked as a robot
   user. Use that username and password below.


2. Get into a python3 environment with requests installed


3. Review this script and edit the applicable variables, like...

    CODALAB_URL
    USERNAME
    PASSWORD
    ...


4. Execute the contents of this script with no additional command line arguments with
   the command shown below:

    ./rerun_submission.py

   The script is built to assist the user in the selection of the submission that will be re-run.


5. After selecting a submission id from the list shown in the previous step, add that id to
   the command as a positional argument as shown below.

    ./rerun_submission.py 42

   The script will assist the user in the selection of a task id.


5. After selecting a submission id and a task id, run the command again with both arguments to
   see a demonstration of a robot user re-running a submission on a specific task.

   e.g.

   ./rerun_submission.py 42 a217a322-6ddf-400c-ac7d-336a42863724
"""
# ----------------------------------------------------------------------------
# Configure these
# ----------------------------------------------------------------------------
CODALAB_URL = 'http://localhost/'
USERNAME = 'admin'
PASSWORD = 'admin'


# ----------------------------------------------------------------------------
# Script start..
# ----------------------------------------------------------------------------
from urllib.parse import urljoin  # noqa: E402
from sys import argv, exit              # noqa: E402,E261  # Ignore E261 to line up these noqa
import requests                   # noqa: E402,E261  # Ignore E261 to line up these noqa


SUBMISSION_ID = None
TASK_KEY = None
MODE = 0

if len(argv) > 1:
    SUBMISSION_ID = int(argv[1])
    MODE = 1
if len(argv) > 2:
    TASK_KEY = argv[2]
    MODE = 2


# Login
login_url = urljoin(CODALAB_URL, '/api/api-token-auth/')
resp = requests.post(login_url, {"username": USERNAME, "password": PASSWORD})
if resp.status_code != 200:
    print(f"Failed to login: {resp.content}")
    print('Is the url correct? (http vs https)')
    exit(-1)

# Setup auth headers for the rest of communication
token = resp.json()["token"]
headers = {
    "Authorization": f"Token {token}"
}

if MODE == 0:
    submission_list_url = urljoin(CODALAB_URL, f'/api/submissions/')
    resp = requests.get(submission_list_url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get submissions: {resp.content}")
        exit(-1)
    submissions = resp.json()
    message = """
\n\nPlease select a submission id from the list to be used as a command line argument as such:\n
    ./rerun_submission.py <int:submission_id>\n
It does not fundamentally matter which submission you choose.\n\n
    """
    print(message)
    print('------------------------- Submissions ----------------------')
    print(f"{'id':^10}|{'owner':^20}|{'task id':^10}")
    print('------------------------------------------------------------')
    for sub in submissions:
        task = sub['task']
        if task is not None:
            task = task['id']
        print(f"{sub['id']:^10}|{sub['owner']:^20}|{str(task):^10}")
    print(message)
    exit(0)

elif MODE == 1:
    task_list_url = urljoin(CODALAB_URL, f'/api/tasks/')
    resp = requests.get(task_list_url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get tasks: {resp.content}")
        exit(-1)
    tasks = resp.json()['results']
    message = """
\n\nPlease select a task key from the list to be used as a command line argument as such:\n
    ./rerun_submission.py <int:submission_id> <uuid:task_key>\n
It does not fundamentally matter which task you choose.\n\n
    """
    print(message)
    print('--------------------------------------- Tasks -------------------------------------------')
    print(f"{'key':^50}|{'name':^30}")
    print('-----------------------------------------------------------------------------------------')
    for task in tasks:
        name = task['name'][:20]
        print(f"{task['key']:^50}|{name:^30}")
    print(message)
    exit(0)

"""
Submit it to the competition without creating new dataset.
The submission data is retrieved from the original submission,
And the task data is retrieved from the task passed as a task_pk.
"""
rerun_submission_url = urljoin(CODALAB_URL, f'/api/submissions/{SUBMISSION_ID}/re_run_submission/')
submission_params = {
    "task_key": TASK_KEY,
}

print(f"Rerunning submission {SUBMISSION_ID} using data: {submission_params}")
resp = requests.post(rerun_submission_url, headers=headers, params=submission_params)

NEW_SUBMISSION_ID = None
if resp.status_code in (200, 201):
    print(f"Successfully submitted: {resp.content}")
    NEW_SUBMISSION_ID = resp.json()['id']
else:
    print(f"Error submitting ({resp.status_code}): {resp.content}")
    print("Are you sure this user has `is_bot` checked in the Django Admin?")
    exit(1)

# Get information of new submission
submission_detail_url = urljoin(CODALAB_URL, f'/api/submissions/{NEW_SUBMISSION_ID}/')
resp = requests.get(submission_detail_url, headers=headers)

if resp.status_code in (200, 201):
    NEW_SUBMISSION_TASK_KEY = resp.json()['task']['key']
    print(f'\n\nOld submission pk: {SUBMISSION_ID}')
    print(f'New submission pk: {NEW_SUBMISSION_ID}')
    print(f'\n\nThe new submission should have the same task as the one specified')
    assert TASK_KEY == NEW_SUBMISSION_TASK_KEY
    print(f'Task key specified:      {TASK_KEY}')
    print(f'New submission task key: {NEW_SUBMISSION_TASK_KEY}')
else:
    print(f"Error retrieving details ({resp.status_code}): {resp.content}")
    print("Are you sure this user has `is_bot` checked in the Django Admin?")

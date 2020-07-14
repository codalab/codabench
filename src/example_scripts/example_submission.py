#!/usr/bin/env python3
"""
Overview
========
This script leverages the "robot submissions" feature which allows someone to make
unlimited submissions to a competition. An example use case is the ChaGrade teaching
website: student submissions are made and scores returned via robot submissions.

Usage
=====

1. Create a competition that allows robots, and create a user marked as a robot
   user. Use that username and password below.

2. Get into a python3 environment with requests installed

3. Review this script and edit the applicable variables, like...

    CODALAB_URL
    USERNAME
    PASSWORD
    ...

4. Then execute the contents of this script:

    ./example_submission.py
"""
# ----------------------------------------------------------------------------
# Configure these
# ----------------------------------------------------------------------------
CODALAB_URL = 'http://localhost/'
USERNAME = 'admin'
PASSWORD = 'admin'
PHASE_ID = 0
SUBMISSION_ZIP_PATH = '../tests/functional/test_files/submission.zip'


# ----------------------------------------------------------------------------
# Script start..
# ----------------------------------------------------------------------------
from urllib.parse import urljoin  # noqa: E402
import requests                   # noqa: E402,E261  # Ignore E261 to line up these noqa


# Login
login_url = urljoin(CODALAB_URL, '/api/api-token-auth/')
resp = requests.post(login_url, {"username": USERNAME, "password": PASSWORD})
if resp.status_code != 200:
    print(f"Failed to login: {resp.content}")
    exit(-1)

# Setup auth headers for the rest of communication
token = resp.json()["token"]
headers = {
    "Authorization": f"Token {token}"
}

# Check if we can make a submission
can_make_sub_url = urljoin(CODALAB_URL, f'/api/can_make_submission/{PHASE_ID}/')
resp = requests.get(can_make_sub_url, headers=headers)

if resp.json()['can']:
    # Create + Upload our dataset
    datasets_url = urljoin(CODALAB_URL, '/api/datasets/')
    datasets_payload = {
        "type": "submission",
        "request_sassy_file_name": "submission.zip",
    }
    resp = requests.post(datasets_url, datasets_payload, headers=headers)
    if resp.status_code != 201:
        print(f"Failed to create dataset: {resp.content}")
        exit(-2)

    dataset_data = resp.json()
    sassy_url = dataset_data["sassy_url"].replace('docker.for.mac.localhost', 'localhost')  # switch URLs for local testing
    resp = requests.put(sassy_url, data=open(SUBMISSION_ZIP_PATH, 'rb'), headers={'Content-Type': 'application/zip'})
    if resp.status_code != 200:
        print(f"Failed to upload dataset: {resp.content} to {sassy_url}")
        exit(-3)

    # Submit it to the competition
    submission_url = urljoin(CODALAB_URL, '/api/submissions/')
    submission_payload = {"phase": PHASE_ID, "data": dataset_data["key"]}
    print(f"Making submission using data: {submission_payload}")
    requests.post(submission_url, submission_payload, headers=headers)

else:
    print(f"Failed to create submission: {resp.json()['reason']}")

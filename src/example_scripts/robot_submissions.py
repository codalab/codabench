#!/usr/bin/env python3
"""
Overview
========
This script leverages the "robot submissions" feature which allows someone to make
unlimited submissions to a competition. An example use case is the ChaGrade teaching
website: student submissions are made and scores returned via robot submissions.

Usage
=====

Get into a python3 environemnt with requests installed

Review this script and edit the applicable variables, like...

    CODALAB_URL
    USERNAME
    PASSWORD
    ...

Then execute the contents of this script:

    ./robot_submissions.py
"""
# ----------------------------------------------------------------------------
# Configure these
# ----------------------------------------------------------------------------
CODALAB_URL = 'http://localhost/'
USERNAME = 'admin'
PASSWORD = 'admin'
# COMPETITION_ID = 11
PHASE_ID = 12
SUBMISSION_ZIP_PATH = '../tests/functional/test_files/submission.zip'


# ----------------------------------------------------------------------------
# Script start..
# ----------------------------------------------------------------------------
from urllib.parse import urljoin
import requests

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

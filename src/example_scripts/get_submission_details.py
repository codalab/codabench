#!/usr/bin/env python3
"""
Overview
========
This script is designed to find submission information. It's main purpose is to demonstrate
how to programmatically find submission information.

Usage
=====

1. Run the script with a phase ID as the only argument to find all submissions on that phase.

    ./get_submission_details.py 1

2. Find the submission you would like detailed information about.

3. Run the script again with the phase ID as the first argument and the submission ID as the second
   argument to see a detailed submission object.

    ./get_competition_details.py 1 1
"""

from sys import argv              # noqa: E402,E261  # Ignore E261 to line up these noqa
from operator import itemgetter   # noqa: E402,E261
from urllib.parse import urljoin  # noqa: E402,E261
import requests                   # noqa: E402,E261
from pprint import pprint         # noqa: E402,E261


CODALAB_URL = 'http://localhost/'
USERNAME = 'admin'
PASSWORD = 'admin'
PHASE_ID = None
SUBMISSION_ID = None
MODE = None

if len(argv) > 1:
    PHASE_ID = int(argv[1])
    MODE = 1
if len(argv) > 2:
    SUBMISSION_ID = int(argv[2])
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

if MODE == 1:
    submissions_list_url = urljoin(CODALAB_URL, f'/api/submissions/')
    resp = requests.get(submissions_list_url, {"phase": PHASE_ID}, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get submissions: {resp.content}")
        exit(-3)

    submissions = sorted(resp.json(), key=itemgetter('id'))

    print('\n--------------------- Submissions -----------------------')
    print('  id  |  creator               |  creation date')
    print('---------------------------------------------------------')
    for s in submissions:
        print(f"{s['id']:>4}  |  {s['owner']:<20}  |  {s['created_when']}")
    print()

elif MODE == 2:
    submissions_detail_url = urljoin(CODALAB_URL, f'/api/submissions/{SUBMISSION_ID}')
    resp = requests.get(submissions_detail_url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get submission: {resp.content}")
        exit(-3)

    print('-------------------')
    print('Submission Object:')
    print('-------------------\n')
    pprint(resp.json())
    print()

    submissions_get_details_url = urljoin(CODALAB_URL, f'/api/submissions/{SUBMISSION_ID}/get_details')
    resp = requests.get(submissions_get_details_url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get submission: {resp.content}")
        exit(-3)

    print('-------------------------------')
    print('Submission get_details Object:')
    print('-------------------------------\n')
    pprint(resp.json())
    print()

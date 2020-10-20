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
import getopt
from operator import itemgetter   # noqa: E402,E261
from urllib.parse import urljoin  # noqa: E402,E261
import requests                   # noqa: E402,E261
from pprint import pprint         # noqa: E402,E261


# ----------------------------------------------------------------------------
# Help (-h, --help)
# ----------------------------------------------------------------------------
def print_help():
    help_commands =[
        ["-h, --help", "Print Help (this message) and exit"],
        ["-p, --phase <phase-id>", "Phase ID/PK to select"],
        ["-s, --submission <submission-id>", "Submission ID/PK to select"],
        ["-v, --verbose", "Enable Verbose Output"]
    ]
    usage = [
        [f"{argv[0]} -p <id>", "Show table of submissions on a phase"],
        [f"{argv[0]} -p <id> -s <id>", "Get Details of selected submission"],
        [f"{argv[0]} -p <id> -s <id> -v", "TODO: Explain Verbose Output"],
     ]
    print("Overview:\n    This script is designed to find submission information.\n    "
          "It's main purpose is to demonstrate how to programmatically find submission information.\n")
    print("Usage:")
    for use in usage:
        print("    %-55s %-45s" % (use[0], use[1]))
    print("\nArguments:")
    for command in help_commands:
        print("    %-55s %-45s" % (command[0], command[1]))
    exit(0)

# ----------------------------------------------------------------------------
# Configure these
# ----------------------------------------------------------------------------
CODALAB_URL = 'http://localhost/'
USERNAME = 'admin'
PASSWORD = 'admin'


# ----------------------------------------------------------------------------
# Script start..
# ----------------------------------------------------------------------------
PHASE_ID = SUBMISSION_ID = DETAIL = None

short_options = "hp:s:v"
long_options = ["help", "phase=", "submission=", "verbose"]
argument_list = argv[1:]

try:
    arguments, values = getopt.getopt(argument_list, short_options, long_options)
except getopt.error as err:
    # Output error, and return with an error code
    print(str(err))
    exit(2)

# Evaluate given options
for current_argument, current_value in arguments:
    if current_argument in ("-v", "--verbose"):
        print("Enabling verbose mode")
    elif current_argument in ("-h", "--help"):
        print_help()
    elif current_argument in ("-p", "--phase"):
        PHASE_ID = int(current_value)
    elif current_argument in ("-s", "--submission"):
        SUBMISSION_ID = int(current_value)

# exit(0)
#
# if len(argv) > 1:
#     PHASE_ID = int(argv[1])
# if len(argv) > 2:
#     SUBMISSION_ID = int(argv[2])

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

if PHASE_ID and not SUBMISSION_ID:
    submissions_list_url = urljoin(CODALAB_URL, f'/api/submissions/')
    resp = requests.get(submissions_list_url, {"phase": PHASE_ID}, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get submissions: {resp.content}")
        exit(-2)

    submissions = sorted(resp.json(), key=itemgetter('id'))

    print('\n--------------------- Submissions -----------------------')
    print('  id  |  creator               |  creation date')
    print('---------------------------------------------------------')
    for s in submissions:
        print(f"{s['id']:>4}  |  {s['owner']:<20}  |  {s['created_when']}")
    print()

elif PHASE_ID and SUBMISSION_ID:
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

else:
    print('ERROR: Phase ID missing! Phase ID is required as a command line argument.')

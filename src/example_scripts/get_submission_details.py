#!/usr/bin/env python3
"""
Overview
========
This script is designed to find submission information. It's main purpose is to demonstrate
how to programmatically find submission information.

Usage
=====
OUTDATED: USE the -h switch in the command line
1. Run the script with a phase ID as the only argument to find all submissions on that phase.

    ./get_submission_details.py 1

2. Find the submission you would like detailed information about.

3. Run the script again with the phase ID as the first argument and the submission ID as the second
   argument to see a detailed submission object.

    ./get_competition_details.py 1 1
"""
import json
from sys import argv  # noqa: E402,E261  # Ignore E261 to line up these noqa
import os
import getopt
from operator import itemgetter  # noqa: E402,E261
from urllib.parse import urljoin  # noqa: E402,E261
import requests  # noqa: E402,E261
from pprint import pprint  # noqa: E402,E261
import tempfile
import zipfile


# ----------------------------------------------------------------------------
# Help (-h, --help)
# ----------------------------------------------------------------------------
def print_help():
    help_commands = [
        ["-h, --help", "Print Help (this message) and exit"],
        ["-p, --phase <phase-id>", "Phase ID/PK to select"],
        ["-s, --submission <submission-id>", "Submission ID/PK to select"],
        ["-v, --verbose", "Download Verbose Output"],
        ["-o, --output", "Change directory to save Verbose Output"],
    ]
    usage = [
        [f"{argv[0]} -p <id>", "Show table of submissions on a phase"],
        [f"{argv[0]} -s <id>", "Get Details of selected submission"],
        [f"{argv[0]} -s <id> -v", "Download Submission, Metadata, and logs to zip file"],
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
PHASE_ID = SUBMISSION_ID = None
VERBOSE = False
CURRENT_DIR = os.getcwd()

short_options = "hp:s:vo:"
long_options = ["help", "phase=", "submission=", "verbose", "output="]
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
        VERBOSE = True
    elif current_argument in ("-h", "--help"):
        print_help()
    elif current_argument in ("-p", "--phase"):
        PHASE_ID = int(current_value)
    elif current_argument in ("-s", "--submission"):
        SUBMISSION_ID = int(current_value)
    elif current_argument in ("-o", "--output"):
        os.chdir(current_value)
        CURRENT_DIR = os.getcwd()

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


# If importing this, make sure to call .cleanup() in response
def get_verbose(SUBMISSION_ID):
    submissions_detail_url = urljoin(CODALAB_URL, f'/api/submissions/{SUBMISSION_ID}')
    resp = requests.get(submissions_detail_url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get submission: {resp.content}")
        exit(-3)
    resp_json = resp.json()

    submissions_get_details_url = urljoin(CODALAB_URL, f'/api/submissions/{SUBMISSION_ID}/get_details')
    detail_resp = requests.get(submissions_get_details_url, headers=headers)
    if detail_resp.status_code != 200:
        print(f"Failed to get submission: {detail_resp.content}")
        exit(-3)
    detail_resp_json = detail_resp.json()

    url = detail_resp_json["data_file"]
    # NEEDED FOR DEV ENVIRONMENT
    url = url.replace("docker.for.mac.", '')
    r_zip = requests.get(url)
    temp_dir = tempfile.TemporaryDirectory()
    with open(f'{temp_dir.__enter__()}/submission.zip', 'wb') as file:
        file.write(r_zip.content)
    with open(f'{temp_dir.__enter__()}/submission.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(resp_json, ensure_ascii=False, indent=4))
    with open(f'{temp_dir.__enter__()}/submission_detail.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(detail_resp_json, ensure_ascii=False, indent=4))
    for log in detail_resp_json['logs']:
        with open(f'{temp_dir.__enter__()}/{log["name"]}.txt', 'w', encoding='utf-8') as file:
            url = log["data_file"]
            # NEEDED FOR DEV ENVIRONMENT
            url = url.replace("docker.for.mac.", '')
            resp = requests.get(url)
            resp.encoding = 'utf-8'
            file.write(resp.text)

    return temp_dir


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

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

elif SUBMISSION_ID and VERBOSE:
    temp_dir = get_verbose(SUBMISSION_ID)
    files = os.listdir(temp_dir.__enter__())
    zip_dir = f'{CURRENT_DIR}/submission-{SUBMISSION_ID}.zip'
    with zipfile.ZipFile(zip_dir, 'w') as zipObj:
        for file in files:
            zipObj.write(f'{temp_dir.__enter__()}/{file}', arcname=file)
    print(f"Saved Output to: {zip_dir}")
    temp_dir.cleanup()


elif SUBMISSION_ID:
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
    print('No command given. Try --help')

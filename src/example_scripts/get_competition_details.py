#!/usr/bin/env python3
"""
Overview
========
This script is designed to list competition information. It's main purpose is to help find
the phase id to be used in the 'example_submission.py' script.

Usage
=====

1. Run the script with no arguments to list all competitions.

    ./get_competition_details.py

2. Find the competition you would like to test on.

3. Run the script again with competition id as the only argument to find the phase ID.

    ./get_competition_details.py 1

4. If you want to use the task selection feature, run the script a third time with competition id as the first argument,
   and the phase ID as the second argument to get a list of tasks on the phase.

    ./get_competition_details.py 1 1
"""

from sys import argv              # noqa: E402,E261  # Ignore E261 to line up these noqa
from operator import itemgetter   # noqa: E402,E261
from urllib.parse import urljoin  # noqa: E402,E261
import requests                   # noqa: E402,E261


# ----------------------------------------------------------------------------
# Configure this
# ----------------------------------------------------------------------------
CODALAB_URL = 'http://localhost/'


# ----------------------------------------------------------------------------
# Script start..
# ----------------------------------------------------------------------------
COMPETITION_ID = None
PHASE_ID = None
MODE = 0

if len(argv) > 1:
    COMPETITION_ID = int(argv[1])
    MODE = 1
if len(argv) > 2:
    PHASE_ID = int(argv[2])
    MODE = 2

if MODE == 1:
    comp_detail_url = urljoin(CODALAB_URL, f'/api/competitions/{COMPETITION_ID}')
    resp = requests.get(comp_detail_url)
    if resp.status_code != 200:
        print(f"Failed to get competitions: {resp.content}")
        exit(-1)
    data = resp.json()
    comp_title = data['title']
    phases = sorted(data['phases'], key=itemgetter('id'))

    print(f"\nCompetition: {comp_title}\n")
    print('---------- Phases ----------')
    print('  id  |  name')
    print('----------------------------')
    for p in phases:
        print(f"{p['id']:>4}  |  {p['name']}")
    print()

elif MODE == 2:
    comp_detail_url = urljoin(CODALAB_URL, f'/api/competitions/{COMPETITION_ID}')
    resp = requests.get(comp_detail_url)
    if resp.status_code != 200:
        print(f"Failed to get phase: {resp.content}")
        exit(-2)
    data = resp.json()

    selected_phase = None
    for phase in data['phases']:
        if phase['id'] == PHASE_ID:
            selected_phase = phase
            break

    comp_title = selected_phase['name']
    phases = sorted(data['phases'], key=itemgetter('id'))

    print(f"\nCompetition: {comp_title}\n")
    print('----------------- Tasks ----------------')
    print('  id  |  name')
    print('----------------------------------------')
    for t in selected_phase['tasks']:
        print(f"{t['id']:>4}  |  {t['name']}")
    print()

else:
    comp_list_url = urljoin(CODALAB_URL, f'/api/competitions/')
    resp = requests.get(comp_list_url)
    if resp.status_code != 200:
        print(f"Failed to get competitions: {resp.content}")
        exit(-3)
    competitions = sorted(resp.json(), key=itemgetter('id'))

    print('\n------------------ Competitions ------------------')
    print('  id  |  creator               |  name')
    print('--------------------------------------------------')
    for c in competitions:
        print(f"{c['id']:>4}  |  {c['created_by']:<20}  |  {c['title']}")
    print()

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
"""

from sys import argv              # noqa: E402,E261  # Ignore E261 to line up these noqa
from operator import itemgetter   # noqa: E402,E261
from urllib.parse import urljoin  # noqa: E402,E261
import requests                   # noqa: E402,E261

CODALAB_URL = 'http://localhost/'
COMPETITION_ID = None
PHASE_MODE = False

if len(argv) > 1:
    COMPETITION_ID = int(argv[1])
    PHASE_MODE = True



if PHASE_MODE:
    comp_detail_url = urljoin(CODALAB_URL, f'/api/competitions/{COMPETITION_ID}')
    resp = requests.get(comp_detail_url).json()
    comp_title = resp['title']
    phases = sorted(resp['phases'], key=itemgetter('id'))

    print(f"\nCompetition: {comp_title}\n")
    print('---------- Phases ----------')
    print('  id  |  name')
    print('----------------------------')
    for p in phases:
        print(f"{p['id']:>4}  |  {p['name']}")
    print()

else:
    comp_list_url = urljoin(CODALAB_URL, f'/api/competitions/')
    competitions = sorted(requests.get(comp_list_url).json(), key=itemgetter('id'))

    print('\n------------------ Competitions ------------------')
    print('  id  |  creator               |  name')
    print('--------------------------------------------------')
    for c in competitions:
        print(f"{c['id']:>4}  |  {c['created_by']:<20}  |  {c['title']}")
    print()

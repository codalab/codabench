# --------------------------------------------------
# Imports
# --------------------------------------------------
import os
from competitions.models import Competition

# --------------------------------------------------
# Setting constants
# --------------------------------------------------
BASE_URL = "https://www.codabench.org/competitions/"
STATISTICS_DIR = "/app/statistics/"
CSV_FILE_NAME = "codabench_competition_statistics.csv"
CSV_PATH = STATISTICS_DIR + CSV_FILE_NAME


def create_codabench_statistics():
    """
    This function prepares a CSV file with all published competitions
    """

    # Create statistics directory if not already createad
    if not os.path.exists(STATISTICS_DIR):
        os.makedirs(STATISTICS_DIR)

    # Write header of the CSV file
    with open(CSV_PATH, 'w', newline='') as output_file:
        # Header for the csv
        header = 'title; description; participants; submissions; year; phases; reward; duration (days); url;\n'
        output_file.write(header)

    # loop over published competitions
    for comp in Competition.objects.filter(published=True):

        # get title
        title = comp.title
        title = clean_string(title)

        # get description
        desc = comp.description
        desc = clean_string(desc)

        # get participants
        num_participants = comp.participants.count()

        # get phases
        phases = comp.phases.all()
        num_phases = len(phases)

        # get submissions
        num_submissions = 0
        for phase in phases:
            num_submissions += phase.submissions.count()

        # get competition first phase year
        year = phases[0].start.year

        # get competition start and end date
        start_date = phases[0].start
        end_date = phases[num_phases - 1].end
        # if last phase has no end date, set end date to last phase start date
        if end_date is None:
            end_date = phases[num_phases - 1].start

        # compute duration of the competition
        duration = (end_date - start_date).days

        # get reward
        reward = comp.reward
        # set reward to empty string if none
        if reward is None:
            reward = ""

        # prepare competition url
        url = f"{BASE_URL}{comp.id}"

        # prepare a row with all the computed information for one competition
        row = '{}; {}; {}; {}; {}; {}; {}; {}; {}; \n'.format(
            title,
            desc,
            num_participants,
            num_submissions,
            year,
            num_phases,
            reward,
            duration,
            url
        )

        # write row in the CSV file
        with open(CSV_PATH, 'a') as output_file:
            output_file.write(row)


def clean_string(text):
    """
    This function cleans an input text
    """
    if ";" in text:
        text = text.replace(";", ",")

    if '\n' in text:
        text = text.replace(r'\n', ' ')

    if '\r' in text:
        text = text.replace(r'\r', ' ')

    text = ''.join(text.splitlines())

    return text

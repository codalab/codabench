"""
This script is created to compute two types of statistics:
    1. Overall platform statistics for a specified year
    2. Overall published competitions statistics

Usage:
    Bash into django console
    ```
    docker compose exec django ./manage.py shell_plus
    ```

    For overall platform statistics
    ```
    from competitions.statistics import create_codabench_statistics
    create_codabench_statistics(year=2024)

    # if year is not specified, current year is used by default
    # a csv file named codabench_statistics_2024.csv is generated in statistics folder (for year=2024)
    ```

    For overall published competitions statistics
    ```
    from competitions.statistics import create_codabench_statistics_published_comps
    create_codabench_statistics_published_comps()

    # a csv file named codabench_statistics_published_comps.csv is generated in statistics folder
    ```
"""

# --------------------------------------------------
# Imports
# --------------------------------------------------
import os
from datetime import datetime
from competitions.models import Competition, Submission, CompetitionParticipant
from profiles.models import User

# --------------------------------------------------
# Setting constants
# --------------------------------------------------
BASE_URL = "https://www.codabench.org/competitions/"
STATISTICS_DIR = "/app/statistics/"


def create_codabench_statistics(year=None):
    """
    This function prepares a CSV file with different statistics per month
    """

    # Set year to current year if None
    if year is None:
        year = datetime.now().year

    # Create statistics directory if not already createad
    if not os.path.exists(STATISTICS_DIR):
        os.makedirs(STATISTICS_DIR)

    rows_dict = {}

    # Initialize sets for tracking total of users, participants and submissions
    total_users = set()
    total_participants = set()
    total_submissions = set()

    # Loop over months
    for month in range(1, 13):

        # count total competitions
        tota_competitions_count = Competition.objects.filter(created_when__year=year, created_when__month=month).count()
        rows_dict.setdefault("total_competitions", []).append(tota_competitions_count)

        # count public competitions
        public_competitions_count = Competition.objects.filter(created_when__year=year, created_when__month=month, published=True).count()
        rows_dict.setdefault("public_competitions", []).append(public_competitions_count)

        # count private competitions
        private_competitions_count = Competition.objects.filter(created_when__year=year, created_when__month=month, published=False).count()
        rows_dict.setdefault("private_competitions", []).append(private_competitions_count)

        # Count new users
        new_users_count = User.objects.filter(date_joined__year=year, date_joined__month=month).count()
        rows_dict.setdefault("new_users", []).append(new_users_count)

        # Count total users (including the current month)
        new_user_ids = set(User.objects.filter(date_joined__year=year, date_joined__month=month).values_list('id', flat=True))
        total_users.update(new_user_ids)
        rows_dict.setdefault("total_users", []).append(len(total_users))

        # Count new participants
        new_participants_count = CompetitionParticipant.objects.filter(competition__created_when__year=year, competition__created_when__month=month).count()
        rows_dict.setdefault("new_participants", []).append(new_participants_count)

        # Count total participants (including the current month)
        new_participants_ids = set(CompetitionParticipant.objects.filter(competition__created_when__year=year, competition__created_when__month=month).values_list('id', flat=True))
        total_participants.update(new_participants_ids)
        rows_dict.setdefault("total_participants", []).append(len(total_participants))

        # Count new submissions
        new_submissions_count = Submission.objects.filter(created_when__year=year, created_when__month=month).count()
        rows_dict.setdefault("new_submissions", []).append(new_submissions_count)

        # Submissions per day = total submissions/30
        submissions_per_day = 0
        if new_submissions_count > 0:
            submissions_per_day = int(new_submissions_count / 30)
        rows_dict.setdefault("submissions_per_day", []).append(submissions_per_day)

        # Count successful submissions (i.e., those that are finished)
        successful_submissions = Submission.objects.filter(created_when__year=year, created_when__month=month, status=Submission.FINISHED).count()
        rows_dict.setdefault("finished_submissions", []).append(successful_submissions)

        # Count failed submissions (i.e., those that are failed)
        failed_submissions = Submission.objects.filter(created_when__year=year, created_when__month=month, status=Submission.FAILED).count()
        rows_dict.setdefault("failed_submissions", []).append(failed_submissions)

        # Count total submissions (including the current month)
        new_submissions_ids = set(Submission.objects.filter(created_when__year=year, created_when__month=month).values_list('id', flat=True))
        total_submissions.update(new_submissions_ids)
        rows_dict.setdefault("total_submissions", []).append(len(total_submissions))

    # Set CSV file and path
    CSV_FILE_NAME = f"codabench_statistics_{year}.csv"
    CSV_PATH = STATISTICS_DIR + CSV_FILE_NAME

    # Define month abbreviations
    month_abbr = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Open the CSV file in write mode
    with open(CSV_PATH, 'w') as output_file:
        # Write the header row only once if the file is empty
        if output_file.tell() == 0:
            header = f"{year}; " + "; ".join(month_abbr) + "; Total \n"
            output_file.write(header)

        # Loop over each metric in the rows_dict and write the corresponding row
        for metric, values in rows_dict.items():

            # for total_users, total_participants, and total_submissions
            # total is the last value
            # for others total is the sum
            if metric in ["total_users", "total_participants", "total_submissions"]:
                total = values[-1]
            else:
                # Calculate the total for the metric (sum of all monthly counts)
                total = sum(values)

            # Create a row with the metric name followed by the values for each month
            row = f"{metric}; " + "; ".join(map(str, values)) + f"; {total} \n"
            output_file.write(row)


def create_codabench_statistics_published_comps():
    """
    This function prepares a CSV file with all published competitions
    """

    # Set CSV file and path
    CSV_FILE_NAME = "codabench_statistics_published_comps.csv"
    CSV_PATH = STATISTICS_DIR + CSV_FILE_NAME

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
        else:
            reward = clean_string(reward)

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

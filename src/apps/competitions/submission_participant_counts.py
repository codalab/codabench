"""
This script is created to fill newly added fields in the competition modal with the correct data
The new fields are:
    - submissions_count
    - participants_count

This script should be used only after the new changes are deployed on the server.

Usage:
    Bash into django console
    ```
    docker compose exec django ./manage.py shell_plus
    ```

    Import and call the function
    ```
    from competitions.submission_participant_counts import compute_submissions_participants_counts
    compute_submissions_participants_counts()
    ```
"""
from competitions.models import Competition, CompetitionParticipant, Phase, Submission


def compute_submissions_participants_counts():
    """
    This function counts submissions and participants of competitions and updates all competitions
    """
    competitions = Competition.objects.all()

    for competition in competitions:
        # Count participants for the competition
        participants_count = CompetitionParticipant.objects.filter(competition=competition).count()

        # Get all phases related to the competition
        phases = Phase.objects.filter(competition=competition)

        # Count submissions across all phases of the competition
        submissions_count = Submission.objects.filter(phase__in=phases, parent__isnull=True).count()

        # Update the competition fields
        competition.participants_count = participants_count
        competition.submissions_count = submissions_count
        try:
            competition.save()
        except Exception as e:
            print(f"Fail for competition {competition.pk}")
            print(e)

    print(f"{len(competitions)} Competitions updated successfully!")

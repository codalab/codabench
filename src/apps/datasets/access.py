from competitions.models import CompetitionParticipant, Phase
from datasets.models import Data


TASK_DATASET_PHASE_LOOKUPS = {
    Data.INPUT_DATA: "tasks__input_data",
    Data.REFERENCE_DATA: "tasks__reference_data",
    Data.INGESTION_PROGRAM: "tasks__ingestion_program",
    Data.SCORING_PROGRAM: "tasks__scoring_program",
}

TASK_DATASET_COMPETITION_FLAGS = {
    Data.INPUT_DATA: "make_input_data_available",
    Data.INGESTION_PROGRAM: "make_programs_available",
    Data.SCORING_PROGRAM: "make_programs_available",
}


def phase_is_hidden_from_participants(phase):
    leaderboard = getattr(phase, "leaderboard", None)
    # Treat blind-output phases as hidden for downloadable assets too.
    return bool(
        phase.hide_output
        or phase.hide_prediction_output
        or phase.hide_score_output
        or (leaderboard and leaderboard.hidden)
    )


def user_is_approved_participant(user, competition):
    if competition is None or not getattr(user, "is_authenticated", False):
        return False

    participant_status = getattr(competition, "participant_status", None)
    if participant_status is not None:
        return participant_status == CompetitionParticipant.APPROVED

    return competition.participants.filter(
        user=user,
        status=CompetitionParticipant.APPROVED,
    ).exists()


def user_can_access_competition_phase_resource(user, phase):
    competition = phase.competition
    if competition is None:
        return False

    if competition.user_has_admin_permission(user):
        return True

    if not user_is_approved_participant(user, competition):
        return False

    return not phase_is_hidden_from_participants(phase)


def user_can_access_task_solution(user, phase, solution):
    if solution is None:
        return False

    return user_can_access_competition_phase_resource(user, phase)


def user_can_access_task_dataset(user, phase, dataset):
    if dataset is None:
        return False

    if dataset.is_public:
        return True

    if getattr(user, "is_authenticated", False) and dataset.created_by_id == user.id:
        return True

    competition = phase.competition
    if competition is None:
        return False

    if competition.user_has_admin_permission(user):
        return True

    if not user_is_approved_participant(user, competition):
        return False

    if dataset.type == Data.REFERENCE_DATA:
        return False

    if phase_is_hidden_from_participants(phase):
        return False

    availability_flag = TASK_DATASET_COMPETITION_FLAGS.get(dataset.type)
    if availability_flag is None:
        return False

    return getattr(competition, availability_flag, False)


def user_can_download_dataset(user, dataset):
    if dataset.is_public:
        return True

    if getattr(user, "is_authenticated", False) and dataset.created_by_id == user.id:
        return True

    for phase in _get_task_dataset_phases(dataset):
        if user_can_access_task_dataset(user, phase, dataset):
            return True

    for phase in _get_phase_resource_phases(dataset):
        if user_can_access_competition_phase_resource(user, phase):
            return True

    return False


def _get_task_dataset_phases(dataset):
    lookup = TASK_DATASET_PHASE_LOOKUPS.get(dataset.type)
    if lookup is None:
        return Phase.objects.none()

    return Phase.objects.filter(**{lookup: dataset}).select_related(
        "competition",
        "leaderboard",
    ).distinct()


def _get_phase_resource_phases(dataset):
    if dataset.type == Data.PUBLIC_DATA:
        return dataset.phase_public_data.select_related("competition", "leaderboard").all()

    if dataset.type == Data.STARTING_KIT:
        return dataset.phase_starting_kit.select_related("competition", "leaderboard").all()

    if dataset.type == Data.SOLUTION:
        return Phase.objects.filter(tasks__solutions__data=dataset).select_related(
            "competition",
            "leaderboard",
        ).distinct()

    return Phase.objects.none()

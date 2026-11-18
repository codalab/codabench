from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datasets.models import Data
from datasets.dataset_deletion import DatasetDeleter
from tasks.models import Task
from competitions.models import Submission
import logging
logger = logging.getLogger(__name__)


def _unused_datasets(user):
    """
    Returns the user's unused datasets and programs: the ones "Delete unused datasets/programs" deletes.
    The unused datasets counter uses it too, so the counter shows what the button deletes.

    Submissions, bundles, public data, starting kits and solutions are left out.
    """
    return Data.objects.filter(
        Q(created_by=user) &
        ~Q(type=Data.SUBMISSION) &
        ~Q(type=Data.COMPETITION_BUNDLE) &
        ~Q(type=Data.PUBLIC_DATA) &
        ~Q(type=Data.STARTING_KIT) &
        ~Q(type=Data.SOLUTION)
    ).exclude(
        Q(task_ingestion_programs__isnull=False) |
        Q(task_input_datas__isnull=False) |
        Q(task_reference_datas__isnull=False) |
        Q(task_scoring_programs__isnull=False)
    )


def _unused_submissions(user):
    """
    Returns the user's unused submission zips: the ones "Delete unused submissions" deletes.
    The unused submissions counter uses it too, so the counter shows what the button deletes.
    """
    return Data.objects.filter(
        Q(created_by=user) &
        Q(type=Data.SUBMISSION) &
        Q(competition__isnull=True)
    )


def _unused_starting_kits(user):
    """
    Returns the user's unused starting kits: the ones "Delete unused starting kits" deletes.
    The unused starting kits counter uses it too, so the counter shows what the button deletes.
    """
    return Data.objects.filter(
        Q(created_by=user) &
        Q(type=Data.STARTING_KIT) &
        Q(competition__isnull=True) &
        Q(phase_starting_kit__isnull=True)
    )


def _unused_competition_bundles_and_dumps(user):
    """
    Returns the user's unused competition bundles and dumps: the ones "Delete unused competition bundles" deletes.
    The unused competition bundles counter uses it too, so the counter shows what the button deletes.

    Bundles and dumps are both zips of a competition.
    They are unused when they are not linked to an existing competition.
    Examples: a bundle whose competition was deleted, a dump whose competition was deleted.
    """
    return Data.objects.filter(
        Q(created_by=user) &
        Q(type=Data.COMPETITION_BUNDLE) &
        Q(competition__isnull=True) &
        Q(competition_bundles__isnull=True) &
        Q(competition_dump_file__isnull=True)
    )


@api_view(['GET'])
def user_quota_cleanup(request):

    # Get Unused tasks count
    unused_tasks = Task.objects.filter(
        created_by=request.user,
        phases__isnull=True
    ).count()

    # Get Unused datasets and programs count
    unused_datasets_programs = _unused_datasets(request.user).count()

    # Get Unused submissions count
    unused_submissions = _unused_submissions(request.user).count()

    # Get Failed submissions count
    failed_submissions = Submission.objects.filter(
        Q(owner=request.user) &
        Q(status=Submission.FAILED)
    ).count()

    # Get unused starting kits count
    unused_starting_kits = _unused_starting_kits(request.user).count()

    # Get unused competition bundles and dumps
    unused_competition_bundles_and_dumps = _unused_competition_bundles_and_dumps(request.user).count()

    return Response({
        "unused_tasks": unused_tasks,
        "unused_datasets_programs": unused_datasets_programs,
        "unused_submissions": unused_submissions,
        "failed_submissions": failed_submissions,
        "unused_starting_kits": unused_starting_kits,
        "unused_competition_bundles_and_dumps": unused_competition_bundles_and_dumps
    })


@api_view(["GET"])
def user_quota(request):
    quota = request.user.quota
    storage_used = request.user.get_used_storage_space()
    return Response({"quota": quota, "storage_used": storage_used})


@api_view(['DELETE'])
def delete_unused_tasks(request):
    try:

        Task.objects.filter(
            created_by=request.user,
            phases__isnull=True
        ).delete()

        return Response({
            "success": True,
            "message": "Unused tasks deleted successfully"
        })
    except Exception as e:
        logger.error(f"UNUSED TASKS DELETION --- {e}")
        return Response({
            "success": False,
            "message": f"{e}"
        })


@api_view(['DELETE'])
def delete_unused_datasets(request):
    try:
        DatasetDeleter(_unused_datasets(request.user)).delete()

        return Response({
            "success": True,
            "message": "Unused datasets and programs deleted successfully"
        })
    except Exception as e:
        logger.error(f"UNUSED DATASETS DELETION --- {e}")
        return Response({
            "success": False,
            "message": f"{e}"
        })


@api_view(['DELETE'])
def delete_unused_submissions(request):
    try:

        DatasetDeleter(_unused_submissions(request.user)).delete()

        return Response({
            "success": True,
            "message": "Unused submissions deleted successfully"
        })
    except Exception as e:
        logger.error(f"UNUSED SUBMISSIONS DELETION --- {e}")
        return Response({
            "success": False,
            "message": f"{e}"
        })


@api_view(['DELETE'])
def delete_failed_submissions(request):
    try:
        Submission.objects.filter(
            Q(owner=request.user) &
            Q(status=Submission.FAILED)
        ).delete()

        return Response({
            "success": True,
            "message": "Failed submissions deleted successfully"
        })
    except Exception as e:
        logger.error(f"FAILED SUBMISSIONS DELETION --- {e}")
        return Response({
            "success": False,
            "message": f"{e}"
        })


@api_view(['DELETE'])
def delete_unused_starting_kits(request):
    try:
        DatasetDeleter(_unused_starting_kits(request.user)).delete()

        return Response({
            "success": True,
            "message": "Unused starting kits deleted successfully"
        })
    except Exception as e:
        logger.error(f"UNUSED STARTING KITS DELETION --- {e}")
        return Response({
            "success": False,
            "message": f"{e}"
        })


@api_view(['DELETE'])
def delete_unused_competition_bundles_and_dumps(request):
    try:
        DatasetDeleter(_unused_competition_bundles_and_dumps(request.user)).delete()

        return Response({
            "success": True,
            "message": "Unused competition bundles and dumps deleted successfully"
        })
    except Exception as e:
        logger.error(f"UNUSED COMPETITION BUNDLES/DUMPS DELETION --- {e}")
        return Response({
            "success": False,
            "message": f"{e}"
        })

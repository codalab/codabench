from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datasets.models import Data
from tasks.models import Task
from competitions.models import Submission
import logging
logger = logging.getLogger(__name__)


@api_view(['GET'])
def user_quota_cleanup(request):

    # Get Unused tasks count
    unused_tasks = Task.objects.filter(
        created_by=request.user,
        phases__isnull=True
    ).count()

    # Get Unused datasets and programs count
    unused_datasets_programs = Data.objects.filter(
        Q(created_by=request.user) &
        ~Q(type=Data.SUBMISSION) &
        ~Q(type=Data.COMPETITION_BUNDLE)
    ).exclude(
        Q(task_ingestion_programs__isnull=False) |
        Q(task_input_datas__isnull=False) |
        Q(task_reference_datas__isnull=False) |
        Q(task_scoring_programs__isnull=False)
    ).count()

    # Get Unused submissions count
    unused_submissions = Data.objects.filter(
        Q(created_by=request.user) &
        Q(type=Data.SUBMISSION) &
        Q(competition__isnull=True)
    ).count()

    # Get Failed submissions count
    failed_submissions = Submission.objects.filter(
        Q(owner=request.user) &
        Q(status=Submission.FAILED)
    ).count()

    return Response({
        "unused_tasks": unused_tasks,
        "unused_datasets_programs": unused_datasets_programs,
        "unused_submissions": unused_submissions,
        "failed_submissions": failed_submissions
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
        Data.objects.filter(
            Q(created_by=request.user) &
            ~Q(type=Data.SUBMISSION) &
            ~Q(type=Data.COMPETITION_BUNDLE)
        ).exclude(
            Q(task_ingestion_programs__isnull=False) |
            Q(task_input_datas__isnull=False) |
            Q(task_reference_datas__isnull=False) |
            Q(task_scoring_programs__isnull=False)
        ).delete()

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

        Data.objects.filter(
            Q(created_by=request.user) &
            Q(type=Data.SUBMISSION) &
            Q(competition__isnull=True)
        ).delete()

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

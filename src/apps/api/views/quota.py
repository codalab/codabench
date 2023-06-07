from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import OuterRef, Subquery

from datasets.models import Data
from competitions.models import Competition
from tasks.models import Task
from competitions.models import Submission


@api_view(['GET'])
def user_quota_cleanup(request):

    # Get Unused tasks count
    competitions_using_task = Competition.objects.filter(
        Q(phases__tasks__in=OuterRef("id"))
    ).values('id').distinct()
    unused_tasks = Task.objects.filter(
        Q(created_by=request.user)
    ).annotate(
        is_used_by=Subquery(competitions_using_task)
    ).filter(
        is_used_by__isnull=True
    ).count()

    # Get Unused datasets and programs count
    competitions_using_dataset = Competition.objects.filter(
        Q(phases__tasks__ingestion_program=OuterRef("pk")) |
        Q(phases__tasks__input_data=OuterRef("pk")) |
        Q(phases__tasks__reference_data=OuterRef("pk")) |
        Q(phases__tasks__scoring_program=OuterRef("pk"))
    ).values('pk').distinct()
    unused_datasets_programs = Data.objects.filter(
        Q(created_by=request.user) &
        ~Q(type=Data.SUBMISSION) &
        ~Q(type=Data.COMPETITION_BUNDLE)
    ).annotate(
        is_used_by=Subquery(competitions_using_dataset)
    ).filter(
        is_used_by__isnull=True
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


@api_view(['DELETE'])
def delete_unused_tasks(request):
    try:
        competitions_using_task = Competition.objects.filter(
            Q(phases__tasks__in=OuterRef("id"))
        ).values('id').distinct()
        Task.objects.filter(
            Q(created_by=request.user)
        ).annotate(
            is_used_by=Subquery(competitions_using_task)
        ).filter(
            is_used_by__isnull=True
        ).delete()

        return Response({
            "success": True,
            "message": "Unused tasks deleted successfully"
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": e
        })


@api_view(['DELETE'])
def delete_unused_datasets(request):
    try:
        competitions_using_dataset = Competition.objects.filter(
            Q(phases__tasks__ingestion_program=OuterRef("pk")) |
            Q(phases__tasks__input_data=OuterRef("pk")) |
            Q(phases__tasks__reference_data=OuterRef("pk")) |
            Q(phases__tasks__scoring_program=OuterRef("pk"))
        ).values('pk').distinct()
        Data.objects.filter(
            Q(created_by=request.user) &
            ~Q(type=Data.SUBMISSION) &
            ~Q(type=Data.COMPETITION_BUNDLE)
        ).annotate(
            is_used_by=Subquery(competitions_using_dataset)
        ).filter(
            is_used_by__isnull=True
        ).delete()

        return Response({
            "success": True,
            "message": "Unused datasets and programs deleted successfully"
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": e
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
        return Response({
            "success": False,
            "message": e
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
        return Response({
            "success": False,
            "message": e
        })

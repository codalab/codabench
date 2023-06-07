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

    # Get Unused submissions count
    unused_submissions = Data.objects.filter(
        Q(created_by=request.user) &
        Q(type=Data.SUBMISSION) &
        Q(competition__isnull=True)
    ).count()

    # Get Unused datasets and programs
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

    # Get Unused tasks
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

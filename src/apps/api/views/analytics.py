from django.db import IntegrityError, transaction
from uuid import UUID, uuid4
from django.shortcuts import get_object_or_404

from django.db.models import Q, Count, F
from django.contrib.auth import get_user_model
from django.http import Http404
from analytics.orphan_files.persistence import get_current_scan_result
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.filters import BaseFilterBackend
from rest_framework.decorators import api_view
from rest_framework_csv import renderers as r
from competitions.models import Competition, Submission
from analytics.models import OrphanFileCandidate, OrphanFilesJob, StorageUsageHistory, CompetitionStorageDataPoint, UserStorageDataPoint
from api.serializers.analytics import AnalyticsSerializer
from analytics.tasks import scan_orphan_files_task, cleanup_orphan_files_task
from analytics.orphan_files.cleanup import is_allowed_object

import os
import datetime
import pytz
import logging
logger = logging.getLogger(__name__)


User = get_user_model()


def merge_dicts(d1, d2):
    d = {**d1, **d2}
    return d


def build_request_object(model_name, filter_param, time_unit, start_date, end_date, csv, data_key, count_key):
    filter_args = {
        filter_param + '__range': [start_date, end_date]
    }

    count_key = count_key if csv else 'count'
    data_key = data_key if csv else '_datefield'

    output_fields = {
        count_key: Count('pk'),
        data_key: F('datefield')
    }

    return model_name.objects.filter(**filter_args).dates(filter_param, time_unit).values(**output_fields)


class AnalyticsRenderer(r.CSVRenderer):

    labels = {
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'time_unit': 'Time Unit',
        'registered_user_count': 'Registered User Count',
        'competition_count': 'Competition Count',
        'competitions_published_count': 'Competitions Published Count',
        'submissions_made_count': 'Submissions Made Count',
        'users_data_date': 'Users Data Date',
        'users_data_count': 'Users Data Count',
        'competitions_data_date': 'Competitions Data Date',
        'competitions_data_count': 'Competitions Data Count',
        'submissions_data_date': 'Submissions Data Date',
        'submissions_data_count': 'Submissions Data Count',
    }

    header = list(labels.keys())


class AnalyticsView(APIView):

    """
    get:
        Return the total number of users joined, competitions created, published competitions created, and submissions made within a given time interval. Also returns the number of comps, users, and subs created within the time range for each time unit.
    """

    filter_backends = (BaseFilterBackend,)
    renderer_classes = (JSONRenderer, AnalyticsRenderer,)

    def get(self, request):
        if not request.user.is_superuser:
            raise Http404()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        time_unit = request.query_params.get('time_unit')
        csv = request.query_params.get('format') == 'csv'

        _start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
        _end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=11, minute=59, second=59, tzinfo=pytz.UTC)

        users = build_request_object(User, 'date_joined', time_unit, _start_date, _end_date, csv, 'users_data_date', 'users_data_count')
        competitions = build_request_object(Competition, 'created_when', time_unit, _start_date, _end_date, csv, 'competitions_data_date', 'competitions_data_count')
        submissions = build_request_object(Submission, 'created_when', time_unit, _start_date, _end_date, csv, 'submissions_data_date', 'submissions_data_count')

        if csv:
            ob = [{
                'start_date': start_date,
                'end_date': end_date,
                'time_unit': time_unit,
                'registered_user_count': User.objects.filter(date_joined__range=[_start_date, _end_date]).count(),
                'competition_count': Competition.objects.filter(created_when__range=[_start_date, _end_date]).count(),
                'competitions_published_count': Competition.objects.filter(published=True, created_when__range=[_start_date, _end_date]).count(),
                'submissions_made_count': Submission.objects.filter(created_when__range=[_start_date, _end_date]).count(),
            }]

            max_len = max(len(users), len(competitions), len(submissions))

            for i in range(max_len):
                d = {}
                for data_list in [users, competitions, submissions]:
                    if i < len(data_list):
                        d = merge_dicts(d, data_list[i])
                if i == 0:
                    ob[i] = merge_dicts(ob[i], d)
                else:
                    ob.append(d)
            serializer = AnalyticsSerializer(data=ob, many=True)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data)

        return Response({
            'registered_user_count': User.objects.filter(date_joined__range=[start_date, end_date]).count(),
            'competition_count': Competition.objects.filter(created_when__range=[start_date, end_date]).count(),
            'competitions_published_count': Competition.objects.filter(published=True, created_when__range=[start_date, end_date]).count(),
            'submissions_made_count': Submission.objects.filter(created_when__range=[start_date, end_date]).count(),
            'users_data': users,
            'competitions_data': competitions,
            'submissions_data': submissions,
            'start_date': start_date,
            'end_date': end_date,
            'time_unit': time_unit,
        })


@api_view(["GET"])
def storage_usage_history(request):
    """
    Gets the storage usage timeline between the 2 provided dates at the given resolution
    """
    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    storage_usage_history = {}
    last_storage_usage_history_snapshot = StorageUsageHistory.objects.order_by("-at_date").first()
    if last_storage_usage_history_snapshot:
        start_date = request.query_params.get("start_date", (datetime.datetime.today() - datetime.timedelta(weeks=4)).strftime("%Y-%m-%d"))
        end_date = request.query_params.get("end_date", datetime.datetime.today().strftime("%Y-%m-%d"))
        resolution = request.query_params.get("resolution", "day")

        query = StorageUsageHistory.objects.filter(
            bucket_name=last_storage_usage_history_snapshot.bucket_name,
            at_date__range=(start_date, end_date),
        ).dates("at_date", resolution).values()
        for su in query.order_by("-at_date"):
            storage_usage_history[su['datefield'].isoformat()] = {
                'total_usage': su['total_usage'],
                'competitions_usage': su['competitions_usage'],
                'users_usage': su['users_usage'],
                'admin_usage': su['admin_usage'],
                'orphaned_file_usage': su['orphaned_file_usage']
            }

    response = {
        "last_storage_calculation_date": last_storage_usage_history_snapshot.created_at.isoformat() if last_storage_usage_history_snapshot else None,
        "storage_usage_history": storage_usage_history
    }

    return Response(response, status=status.HTTP_200_OK)


@api_view(["GET"])
def competitions_usage(request):
    """
    Gets the competitions usage between the 2 provided dates at the given resolution
    """
    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    competitions_usage = {}
    last_competition_storage_snapshot = CompetitionStorageDataPoint.objects.order_by("-at_date").first()
    if last_competition_storage_snapshot:
        start_date = request.query_params.get("start_date", (datetime.datetime.today() - datetime.timedelta(weeks=4)).strftime("%Y-%m-%d"))
        end_date = request.query_params.get("end_date", datetime.datetime.today().strftime("%Y-%m-%d"))
        resolution = request.query_params.get("resolution", "day")

        query = CompetitionStorageDataPoint.objects.filter(
            at_date__range=(start_date, end_date),
            competition__isnull=False
        ).dates("at_date", resolution).values(
            'id',
            'competition__id',
            'competition__title',
            'competition__created_by__username',
            'competition__created_by__email',
            'competition__created_when',
            'datasets_total',
            'datefield'
        )
        for su in query.order_by("-datefield", "competition__id"):
            username = su['competition__created_by__username'] or ("user #" + su['competition__created_by__id']) or "unknown user"
            email = su['competition__created_by__email'] or "no email"
            competitions_usage.setdefault(su['datefield'].isoformat(), {})[su['competition__id']] = {
                'snapshot_id': su['id'],
                'title': su['competition__title'],
                'organizer': username + " (" + email + ")",
                'created_when': su['competition__created_when'],
                'datasets': su['datasets_total'],
            }

    response = {
        "last_storage_calculation_date": last_competition_storage_snapshot.created_at.isoformat() if last_competition_storage_snapshot else None,
        "competitions_usage": competitions_usage
    }

    return Response(response, status=status.HTTP_200_OK)


@api_view(["GET"])
def users_usage(request):
    """
    Gets the users usage between the 2 provided dates at the given resolution
    """
    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    users_usage = {}
    last_user_storage_snapshot = UserStorageDataPoint.objects.order_by("-at_date").first()
    if last_user_storage_snapshot:
        start_date = request.query_params.get("start_date", (datetime.datetime.today() - datetime.timedelta(weeks=4)).strftime("%Y-%m-%d"))
        end_date = request.query_params.get("end_date", datetime.datetime.today().strftime("%Y-%m-%d"))
        resolution = request.query_params.get("resolution", "day")

        query = UserStorageDataPoint.objects.filter(
            at_date__range=(start_date, end_date),
            user__isnull=False
        ).dates("at_date", resolution).values(
            'id',
            'user__id',
            'user__username',
            'user__email',
            'user__date_joined',
            'datasets_total',
            'submissions_total',
            'datefield'
        )
        for su in query.order_by("-datefield", "user__id"):
            username = su['user__username'] or ("user #" + su['user__id']) or "unknown user"
            email = su['user__email'] or "no email"
            users_usage.setdefault(su['datefield'].isoformat(), {})[su['user__id']] = {
                'snapshot_id': su['id'],
                'name': username + " (" + email + ")",
                'date_joined': su['user__date_joined'],
                'datasets': su['datasets_total'],
                'submissions': su['submissions_total'],
            }

    response = {
        "last_storage_calculation_date": last_user_storage_snapshot.created_at.isoformat() if last_user_storage_snapshot else None,
        "users_usage": users_usage
    }

    return Response(response, status=status.HTTP_200_OK)


def get_most_recent_storage_inconsistency_log_file():
    logger = logging.getLogger(__name__)

    log_folder = "/app/logs/"
    try:
        log_files = [f for f in os.listdir(log_folder) if os.path.isfile(os.path.join(log_folder, f))]
    except FileNotFoundError:
        logger.error(f"Folder '{log_folder}' does not exist.")
        return None

    most_recent_log_file = None
    most_recent_datetime = None
    datetime_format = "%Y%m%d-%H%M%S"
    for file in log_files:
        try:
            basename = os.path.basename(file)
            datetime_str = basename[len("db_storage_inconsistency_"):-len(".log")]
            file_datetime = datetime.datetime.strptime(datetime_str, datetime_format)
            if most_recent_datetime is None or file_datetime > most_recent_datetime:
                most_recent_datetime = file_datetime
                most_recent_log_file = file
        except ValueError:
            logger.warning(f"Filename '{file}' does not match the expected format and will be ignored.")

    return most_recent_log_file


ACTIVE_ORPHAN_JOB_STATUSES = (
    OrphanFilesJob.Status.PENDING,
    OrphanFilesJob.Status.STARTED,
    OrphanFilesJob.Status.PROGRESS,
)

ELIGIBLE_CANDIDATE_STATUSES = (
    OrphanFileCandidate.Status.PENDING,
    OrphanFileCandidate.Status.FAILED,
)


def get_active_orphan_job():
    return OrphanFilesJob.objects.filter(
        status__in=ACTIVE_ORPHAN_JOB_STATUSES,
    ).first()


def get_latest_orphan_scan():
    return OrphanFilesJob.objects.filter(
        job_type=OrphanFilesJob.JobType.SCAN,
    ).first()


def serialize_orphan_job(job, include_result=True):
    if job is None:
        return None

    response = {
        "task_id": str(job.task_id),
        "job_type": job.job_type,
        "status": job.status,
        "grace_period_days": job.grace_period_days,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "heartbeat_at": job.heartbeat_at,
        "error": job.error,
        "source_scan_task_id": (
            str(job.source_scan.task_id)
            if job.source_scan_id
            else None
        ),
    }

    if include_result:
        if (
            job.job_type == OrphanFilesJob.JobType.SCAN
            and job.status == OrphanFilesJob.Status.SUCCESS
        ):
            response["result"] = get_current_scan_result(job)
        else:
            response["result"] = job.result

    return response


def orphan_job_conflict_response():
    return Response(
        {
            "detail": "An orphan files job is already running.",
            "active_job": serialize_orphan_job(
                get_active_orphan_job(),
                include_result=False,
            ),
        },
        status=status.HTTP_409_CONFLICT,
    )


def dispatch_orphan_job(job, task, kwargs):
    """
    Dispatch the Celery task using the persistent job UUID.
    """

    def publish():
        try:
            task.apply_async(
                task_id=str(job.task_id),
                kwargs=kwargs,
            )

        except Exception:
            logger.exception(
                "Could not confirm dispatch of orphan job %s",
                job.task_id,
            )

            # Keep the job active because a broker error
            # does not prove that publication failed.
            OrphanFilesJob.objects.filter(
                pk=job.pk,
                status=OrphanFilesJob.Status.PENDING,
            ).update(
                error="Task dispatch could not be confirmed.",
            )

    transaction.on_commit(publish)


@api_view(["GET"])
def current_orphan_files_job(request):
    """
    Restore the current orphan files interface state.
    """
    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    active_job = get_active_orphan_job()

    last_scan = get_latest_orphan_scan()

    last_cleanup = OrphanFilesJob.objects.filter(
        job_type=OrphanFilesJob.JobType.CLEANUP,
    ).first()

    return Response(
        {
            "active_job": serialize_orphan_job(
                active_job,
                include_result=False,
            ),
            "last_scan": serialize_orphan_job(last_scan),
            "last_cleanup": serialize_orphan_job(last_cleanup),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def start_orphan_files_scan(request):
    """
    Create a persistent scan job before dispatching Celery.
    """
    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    grace_period_days = request.data.get(
        "grace_period_days", 7
    )

    if (
        isinstance(grace_period_days, bool)
        or not isinstance(grace_period_days, int)
        or not 0 <= grace_period_days <= 3650
    ):
        return Response(
            {
                "detail": (
                    "grace_period_days must be an integer "
                    "between 0 and 3650"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():

            if get_active_orphan_job():
                return orphan_job_conflict_response()

            job = OrphanFilesJob.objects.create(
                task_id=uuid4(),
                job_type=OrphanFilesJob.JobType.SCAN,
                status=OrphanFilesJob.Status.PENDING,
                grace_period_days=grace_period_days,
            )

            dispatch_orphan_job(
                job=job,
                task=scan_orphan_files_task,
                kwargs={},
            )

    except IntegrityError:
        if get_active_orphan_job():
            return orphan_job_conflict_response()
        raise

    return Response(
        serialize_orphan_job(
            job,
            include_result=False,
        ),
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(["GET"])
def orphan_files_scan_status(request, task_id):
    """
    Return the persistent scan status.
    """
    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    job = get_object_or_404(
        OrphanFilesJob,
        task_id=task_id,
        job_type=OrphanFilesJob.JobType.SCAN,
    )

    return Response(
        serialize_orphan_job(job),
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def start_orphan_files_cleanup(request):
    """
    Create a cleanup job associated with a successful scan.
    """
    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    data = request.data
    mode = data.get("mode", "all")

    if mode not in ("all", "selected"):
        return Response(
            {"detail": "Invalid cleanup mode"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        scan_task_id = UUID(str(data.get("scan_task_id")))

    except (TypeError, ValueError):
        return Response(
            {"detail": "Invalid or missing scan_task_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    selected_objects = None

    if mode == "selected":
        selected_objects = data.get("selected_objects")

        if (
            not isinstance(selected_objects, list)
            or not 1 <= len(selected_objects) <= 100
        ):
            return Response(
                {"detail": "Select between 1 and 100 objects"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        identities = set()

        for item in selected_objects:

            if not isinstance(item, dict):
                return Response(
                    {"detail": "Invalid selected object"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            bucket = item.get("bucket")
            key = item.get("key")

            if not is_allowed_object(bucket, key):
                return Response(
                    {"detail": "Object outside allowed prefixes"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            identities.add((bucket, key))

        if len(identities) != len(selected_objects):
            return Response(
                {"detail": "Duplicate selected objects"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif data.get("selected_objects") is not None:
        return Response(
            {
                "detail": (
                    "selected_objects is only valid "
                    "in selected mode"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():

            if get_active_orphan_job():
                return orphan_job_conflict_response()

            scan = get_object_or_404(
                OrphanFilesJob.objects.select_for_update(),
                task_id=scan_task_id,
                job_type=OrphanFilesJob.JobType.SCAN,
            )

            if scan.status != OrphanFilesJob.Status.SUCCESS:
                return Response(
                    {"detail": "The source scan is not successful"},
                    status=status.HTTP_409_CONFLICT,
                )

            latest_scan = get_latest_orphan_scan()

            if latest_scan.pk != scan.pk:
                return Response(
                    {"detail": "A newer scan exists. Reload the page."},
                    status=status.HTTP_409_CONFLICT,
                )

            candidates = scan.candidates.filter(
                status__in=ELIGIBLE_CANDIDATE_STATUSES,
            )

            if mode == "selected":
                selection = Q()

                for bucket, key in identities:
                    selection |= Q(bucket=bucket, key=key)

                candidates = candidates.filter(selection)

                if candidates.count() != len(identities):
                    return Response(
                        {
                            "detail": (
                                "Some selected objects are no longer "
                                "eligible for cleanup"
                            )
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

            elif not candidates.exists():
                return Response(
                    {"detail": "No remaining orphan files"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            job = OrphanFilesJob.objects.create(
                task_id=uuid4(),
                job_type=OrphanFilesJob.JobType.CLEANUP,
                status=OrphanFilesJob.Status.PENDING,
                grace_period_days=scan.grace_period_days,
                source_scan=scan,
            )

            dispatch_orphan_job(
                job=job,
                task=cleanup_orphan_files_task,
                kwargs={
                    "mode": mode,
                    "selected_objects": selected_objects,
                },
            )

    except IntegrityError:
        if get_active_orphan_job():
            return orphan_job_conflict_response()
        raise

    return Response(
        serialize_orphan_job(
            job,
            include_result=False,
        ),
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(["GET"])
def orphan_files_cleanup_status(request, task_id):
    """
    Return the persistent cleanup status.
    """
    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    job = get_object_or_404(
        OrphanFilesJob,
        task_id=task_id,
        job_type=OrphanFilesJob.JobType.CLEANUP,
    )

    return Response(
        serialize_orphan_job(job),
        status=status.HTTP_200_OK,
    )

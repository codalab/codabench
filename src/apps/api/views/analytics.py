from django.db.models import Count, F
from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.filters import BaseFilterBackend
from rest_framework.decorators import api_view
from rest_framework_csv import renderers as r
from competitions.models import Competition, Submission
from analytics.models import StorageUsageHistory, CompetitionStorageDataPoint, UserStorageDataPoint
from api.serializers.analytics import AnalyticsSerializer
from utils.storage import BundleStorage

import os
import datetime
import coreapi
import pytz
import logging


User = get_user_model()


class SimpleFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        fields = [
            coreapi.Field(
                name='start_date',
                location='query',
                required=True,
                type='string',
                description='Beginning of query interval (inclusive) (YYYY-MM-DD format string)'
            ),
            coreapi.Field(
                name='end_date',
                location='query',
                required=True,
                type='string',
                description='End of query interval (exclusive) (YYYY-MM-DD format string)'
            ),
            coreapi.Field(
                name='time_unit',
                location='query',
                required=True,
                type='string',
                description='Unit of time (choose 1 of month, week, or day)'
            ),
            coreapi.Field(
                name='format',
                location='query',
                required=False,
                type='string',
                description='If csv data is desired set format=csv, otherwise do not set.'
            ),
        ]

        return fields


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

    filter_backends = (SimpleFilterBackend,)
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
            competitions_usage.setdefault(su['datefield'].isoformat(), {})[su['competition__id']] = {
                'snapshot_id': su['id'],
                'title': su['competition__title'],
                'organizer': su['competition__created_by__username'] + " (" + su['competition__created_by__email'] + ")",
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
            users_usage.setdefault(su['datefield'].isoformat(), {})[su['user__id']] = {
                'snapshot_id': su['id'],
                'name': su['user__username'] + " (" + su['user__email'] + ")",
                'date_joined': su['user__date_joined'],
                'datasets': su['datasets_total'],
                'submissions': su['submissions_total'],
            }

    response = {
        "last_storage_calculation_date": last_user_storage_snapshot.created_at.isoformat() if last_user_storage_snapshot else None,
        "users_usage": users_usage
    }

    return Response(response, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_orphan_files(request):
    """
    Get the orphan files based on the last storage analytics
    """

    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    logger = logging.getLogger(__name__)

    # Find most recent file
    most_recent_log_file = get_most_recent_storage_inconsistency_log_file()
    if not most_recent_log_file:
        logger.warning("No storage inconsistency log file found.")
        return Response({"message": "No storage inconsistency log file found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Get the list of orphan files from the content of the most recent log file
    log_folder = "/app/logs/"
    orphan_files_path = get_files_path_from_orphan_log_file(os.path.join(log_folder, most_recent_log_file))

    return Response({"data": orphan_files_path}, status=status.HTTP_200_OK)

@api_view(["DELETE"])
def delete_orphan_files(request):
    """
    Delete all orphan files from the storage based on the last storage analytics
    """

    if not request.user.is_superuser:
        raise PermissionDenied(detail="Admin only")

    logger = logging.getLogger(__name__)
    logger.info("Delete orphan files started")

    # The analytics task generates a db_storage_inconsistency_<date>-<time>.log file that lists, among other things, the orphan files. Let's use it

    # Find most recent file
    most_recent_log_file = get_most_recent_storage_inconsistency_log_file()
    if not most_recent_log_file:
        logger.warning("No storage inconsistency log file found. Nothing will be removed")
        return Response({"message": "No storage inconsistency log file found. Nothing will be removed"}, status=status.HTTP_404_NOT_FOUND)

    # Get the list of orphan files from the content of the most recent log file
    log_folder = "/app/logs/"
    orphan_files_path = get_files_path_from_orphan_log_file(os.path.join(log_folder, most_recent_log_file))

    # Delete those files in batch (max 1000 element at once)
    batch_size = 1000
    for i in range(0, len(orphan_files_path), batch_size):
        batch = orphan_files_path[i:i + batch_size]
        objects_formatted = [{'Key': path} for path in batch]
        BundleStorage.bucket.delete_objects(Delete={'Objects': objects_formatted})

    logger.info("Delete oprhan files finished")
    return Response({"message": "done"}, status=status.HTTP_200_OK)

def get_most_recent_storage_inconsistency_log_file():
    logger = logging.getLogger(__name__)

    log_folder = "/app/logs/"
    try:
        log_files = [f for f in os.listdir(log_folder) if os.path.isfile(os.path.join(log_folder, f))]
    except FileNotFoundError:
        logger.info(f"Folder '{log_folder}' does not exist.")
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

def get_files_path_from_orphan_log_file(log_file_path):
    logger = logging.getLogger(__name__)

    files_path = []

    try:
        with open(log_file_path) as log_file:
            lines = log_file.readlines()
            orphan_files_lines = []
            for i, line in enumerate(lines):
                if "Orphaned files" in line:
                    orphan_files_lines = lines[i + 1:]
                    break

            for orphan_files_line in orphan_files_lines:
                files_path.append(orphan_files_line.split(maxsplit=1)[0])
    except FileNotFoundError:
        logger.error(f"File '{log_file_path}' does not exist.")
    except PermissionError:
        logger.error(f"Permission denied for reading the file '{log_file_path}'.")
    except IOError as e:
        logger.error(f"An I/O error occurred while accessing the file at {log_file_path}: {e}")
    
    return  files_path

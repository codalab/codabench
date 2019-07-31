from django.db.models import Count, F
from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.filters import BaseFilterBackend
from rest_framework_csv import renderers as r
from competitions.models import Competition, Submission
from api.serializers.analytics import AnalyticsSerializer

import datetime
import coreapi
import pytz


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

        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=11, minute=59, second=59, tzinfo=pytz.UTC)

        users = build_request_object(User, 'date_joined', time_unit, start_date, end_date, csv, 'users_data_date', 'users_data_count')
        competitions = build_request_object(Competition, 'created_when', time_unit, start_date, end_date, csv, 'competitions_data_date', 'competitions_data_count')
        submissions = build_request_object(Submission, 'created_when', time_unit, start_date, end_date, csv, 'submissions_data_date', 'submissions_data_count')

        if csv:
            ob = [{
                'start_date': start_date,
                'end_date': end_date,
                'time_unit': time_unit,
                'registered_user_count': User.objects.filter(date_joined__range=[start_date, end_date]).count(),
                'competition_count': Competition.objects.filter(created_when__range=[start_date, end_date]).count(),
                'competitions_published_count': Competition.objects.filter(published=True, created_when__range=[start_date, end_date]).count(),
                'submissions_made_count': Submission.objects.filter(created_when__range=[start_date, end_date]).count(),
            }]

            l = max(len(users), len(competitions), len(submissions))

            for i in range(l):
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

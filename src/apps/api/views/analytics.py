from django.db.models import Count, F
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework_csv import renderers as r
from competitions.models import Competition, Submission


User = get_user_model()


def build_request_object(model_name, filter_param, time_unit, start_date, end_date, csv):
    filter_args = {
        filter_param + '__range': [start_date, end_date]
    }

    data = model_name.objects.filter(**filter_args).dates(filter_param, time_unit).annotate(count=Count('pk')).values('count', x=F('datefield'))

    if csv:
        csv_data = {
            'x': [],
            'count': [],
        }
        for i in data:
            csv_data['x'].append(i['x'])
            csv_data['count'].append(i['count'])
        return csv_data
    else:
        return data


@api_view(['GET'])
@renderer_classes((r.CSVRenderer, JSONRenderer, ))
def analytics_detail(request):
    if not request.user.is_superuser:
        return Response(status=404)

    csv = False
    if request.META.get('HTTP_ACCEPT').split(' ')[0] == 'text/csv;':
        csv = True

    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    time_unit = request.query_params.get('time_unit')

    users = build_request_object(User,'date_joined', time_unit, start_date, end_date, csv)
    competitions = build_request_object(Competition,'created_when', time_unit, start_date, end_date, csv)
    submissions = build_request_object(Submission, 'created_when', time_unit, start_date, end_date, csv)

    if csv:
        data = [users['x'], users['count'], competitions['x'], competitions['count'], submissions['x'], submissions['count']]
        lengths = [len(i) for i in data]

        csv_data = []

        data_remains = True
        i = 0
        while data_remains:
            data_remains = False
            row = []
            for d in range(len(data)):
                if i < lengths[d]:
                    data_remains = True
                    row.append(data[d][i])
                else:
                    row.append(' ')
            csv_data.append(row)
            i += 1

        return Response(
            [
                [
                    'start_date',
                    'end_date',
                    'time_unit',
                    'registered_user_count',
                    'competition_count',
                    'competitions_published_count'
                    'submissions_made_count'
                ],
                [
                    start_date,
                    end_date,
                    time_unit,
                    User.objects.filter(date_joined__range=[start_date, end_date]).count(),
                    Competition.objects.filter(created_when__range=[start_date, end_date]).count(),
                    Competition.objects.filter(published=True, created_when__range=[start_date, end_date]).count(),
                    Submission.objects.filter(created_when__range=[start_date, end_date]).count(),
                ],
                [" "],
                [
                    'users_data date',
                    'users_data count',
                    'competitions_data date',
                    'competitions_data count',
                    'submissions_data date',
                    'submissions_data count'
                ],
                *csv_data,
            ]
        )

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

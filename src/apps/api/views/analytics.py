from django.db.models import Count
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from competitions.models import Competition, Submission


User = get_user_model()


def build_request_object(model_name, filter_param, time_unit, start_date, end_date):
    ob = {}
    filter_args = {
        filter_param + '__range': [start_date, end_date]
    }
    for date in model_name.objects.all().filter(**filter_args).datetimes(filter_param, time_unit):
        if date.year not in ob:
            ob[date.year] = {}
        if date.month not in ob[date.year]:
            if time_unit == 'day':
                ob[date.year][date.month] = {}
            else:
                ob[date.year][date.month] = {
                    'total': 0,
                }
                filter_args = {
                    filter_param + '__month': date.month,
                    filter_param + '__year': date.year,
                }
                this_month = model_name.objects.filter(**filter_args).aggregate(Count('pk'))
                ob[date.year][date.month]['total'] = this_month['pk__count']

        if time_unit == 'day':
            if date.day not in ob[date.year][date.month]:
                ob[date.year][date.month][date.day] = {
                    'total': 0,
                }
            filter_args = {
                filter_param + '__year': date.year,
                filter_param + '__month': date.month,
                filter_param + '__day': date.day,
            }
            this_day = model_name.objects.filter(**filter_args).aggregate(Count('pk'))
            ob[date.year][date.month][date.day]['total'] = this_day['pk__count']

    return ob


@api_view(['GET'])
def analytics_detail(request):
    if not request.user.is_superuser:
        return Response(status=404)

    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    time_unit = request.query_params.get('time_unit')

    users = build_request_object(User,'date_joined', time_unit, start_date, end_date)
    competitions = build_request_object(Competition,'created_when', time_unit, start_date, end_date)
    submissions = build_request_object(Submission, 'created_when', time_unit, start_date, end_date)

    return Response({
        'registered_user_count': User.objects.filter(date_joined__range=[start_date, end_date]).count(),
        'competition_count': Competition.objects.filter(created_when__range=[start_date, end_date]).count(),
        'competitions_published_count': Competition.objects.filter(published=True).filter(created_when__range=[start_date, end_date]).count(),
        'users_data': users,
        'competitions_data': competitions,
        'submissions_data': submissions,
        'start_date': start_date,
        'end_date': end_date,
        'time_unit': time_unit,
    })

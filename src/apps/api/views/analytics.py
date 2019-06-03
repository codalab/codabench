from django.db.models import Count
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from competitions.models import Competition, Submission


User = get_user_model()

@api_view(['GET'])
def analytics_detail(request):
    if not request.user.is_staff:
        return Response(status=404)

    print('query_params', request.query_params)
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    monthly_total_users_joined = {}
    for date in User.objects.all().filter(date_joined__range=[start_date, end_date]).datetimes('date_joined', 'month'):
        if date.year not in monthly_total_users_joined:
            monthly_total_users_joined[date.year] = {}
        users_joined_this_month = User.objects.filter(date_joined__month=date.month,
                                                      date_joined__year=date.year).aggregate(Count('pk'))
        monthly_total_users_joined[date.year][date.strftime("%B")] = users_joined_this_month['pk__count']

    monthly_competitions_created = {}
    for date in Competition.objects.all().filter(created_when__range=[start_date, end_date]).datetimes('created_when', 'month'):
        if date.year not in monthly_competitions_created:
            monthly_competitions_created[date.year] = {}
        competitions_created_this_month = Competition.objects.filter(created_when__month=date.month,
                                                      created_when__year=date.year).aggregate(Count('pk'))
        monthly_competitions_created[date.year][date.strftime("%B")] = competitions_created_this_month['pk__count']

    daily_submissions_created = {}
    for date in Submission.objects.all().filter(created_when__range=[start_date, end_date]).datetimes('created_when', 'day')[0:60]:
        if date.year not in daily_submissions_created:
            daily_submissions_created[date.year] = {}
        if date.month not in daily_submissions_created[date.year]:
            daily_submissions_created[date.year][date.strftime("%B")] = {
                'total': 0,
            }
        submissions_created_this_month = Submission.objects.filter(created_when__month=date.month,
                                                                 created_when__year=date.year).aggregate(Count('pk'))
        submissions_created_this_day = Submission.objects.filter(created_when__day=date.day,
                                                                 created_when__month=date.month,
                                                                     created_when__year=date.year).aggregate(Count('pk'))

        daily_submissions_created[date.year][date.strftime("%B")]['total'] += submissions_created_this_day['pk__count']
        daily_submissions_created[date.year][date.strftime("%B")][date.strftime("%d")] = submissions_created_this_day['pk__count']

    return Response({
        'registered_user_count': User.objects.all().filter(date_joined__range=[start_date, end_date]).count(),
        'competition_count': Competition.objects.all().filter(created_when__range=[start_date, end_date]).count(),
        'competitions_published_count': Competition.objects.filter(published=True).filter(created_when__range=[start_date, end_date]).count(),
        'monthly_total_users_joined': monthly_total_users_joined,
        'monthly_competitions_created': monthly_competitions_created,
        'daily_submissions_created': daily_submissions_created,
        'start_date': start_date,
        'end_date': end_date,
    })

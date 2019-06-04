from django.db.models import Count
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from competitions.models import Competition, Submission
import datetime


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
#        monthly_total_users_joined[date.year][date.strftime("%B")] = users_joined_this_month['pk__count']
        monthly_total_users_joined[date.year][date.month] = users_joined_this_month['pk__count']

    monthly_competitions_created = {}
    for date in Competition.objects.all().filter(created_when__range=[start_date, end_date]).datetimes('created_when', 'month'):
        if date.year not in monthly_competitions_created:
            monthly_competitions_created[date.year] = {}
        competitions_created_this_month = Competition.objects.filter(created_when__month=date.month,
                                                      created_when__year=date.year).aggregate(Count('pk'))
#        monthly_competitions_created[date.year][date.strftime("%B")] = competitions_created_this_month['pk__count']
        monthly_competitions_created[date.year][date.month] = competitions_created_this_month['pk__count']

    daily_submissions_created = {}
    for sub in Submission.objects.all().filter(created_when__range=[start_date, end_date]):
        if sub.created_when.year not in daily_submissions_created:
            daily_submissions_created[sub.created_when.year] = {}
#        if sub.created_when.strftime('%B') not in daily_submissions_created[sub.created_when.year]:
        if sub.created_when.month not in daily_submissions_created[sub.created_when.year]:
#            daily_submissions_created[sub.created_when.year][sub.created_when.strftime("%B")] = {
            daily_submissions_created[sub.created_when.year][sub.created_when.month] = {
                'total': 0,
                'total_file_storage': 0,
            }
#        if sub.created_when.strftime('%d') not in daily_submissions_created[sub.created_when.year][sub.created_when.strftime("%B")]:
#            daily_submissions_created[sub.created_when.year][sub.created_when.strftime("%B")][sub.created_when.strftime("%d")] = {
#        if sub.created_when.day not in daily_submissions_created[sub.created_when.year][sub.created_when.month]:
#            daily_submissions_created[sub.created_when.year][sub.created_when.month][sub.created_when.day] = {
#                'total': 0,
#            }
#        daily_submissions_created[sub.created_when.year][sub.created_when.month][sub.created_when.day]['total'] += 1
        daily_submissions_created[sub.created_when.year][sub.created_when.month]['total'] += 1
        daily_submissions_created[sub.created_when.year][sub.created_when.month]['total_file_storage'] += 73#sub.data.data_file.size

    print('********************************************************* building averages *********************************************************')
    for year in daily_submissions_created:
        for month in daily_submissions_created[year]:
            month_date = datetime.datetime.strptime(str(year) + "{:02d}".format(month) + '01', '%Y%m%d').date()
            days_in_month = (datetime.date(month_date.year if month_date.month < 12 else month_date.year + 1, month_date.month % 12 + 1, 1) - month_date).days
            daily_submissions_created[year][month]['average_submissions_per_day'] = "{:.3f}".format(daily_submissions_created[year][month]['total'] / days_in_month)
            daily_submissions_created[year][month]['average_submissions_size'] = "{:.3f}".format(daily_submissions_created[year][month]['total_file_storage'] / daily_submissions_created[year][month]['total'])

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

from django.db.models import Count
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from competitions.models import Competition


User = get_user_model()

@api_view(['GET'])
def analytics_detail(request):
    if not request.user.is_staff:
        return Response(status=404)

    monthly_total_users_joined = {}
    for date in User.objects.all().datetimes('date_joined', 'month'):
        if date.year not in monthly_total_users_joined:
            monthly_total_users_joined[date.year] = {}
        users_joined_this_month = User.objects.filter(date_joined__month=date.month,
                                                      date_joined__year=date.year).aggregate(Count('pk'))
        monthly_total_users_joined[date.year][date.strftime("%B")] = users_joined_this_month['pk__count']

    return Response({
        'registered_user_count': User.objects.all().count(),
        'competition_count': Competition.objects.all().count(),
        'competitions_published_count': Competition.objects.filter(published=True).count(),
        'monthly_total_users_joined': monthly_total_users_joined,
    })

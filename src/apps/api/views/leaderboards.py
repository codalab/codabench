from rest_framework.viewsets import ModelViewSet

from api.serializers.leaderboards import LeaderboardSerializer
from leaderboards.models import Leaderboard
from rest_framework import permissions


class LeaderboardViewSet(ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer
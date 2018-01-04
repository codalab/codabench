from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet

from api.serializers import leaderboards as serializers
from leaderboards.models import Metric, Column, Leaderboard


class MetricViewSet(ModelViewSet):
    queryset = Metric.objects.all()
    serializer_class = serializers.MetricSerializer
    # permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        print("user trying to save: {}".format(self.request.user))
        # super().perform_create(serializer)


class ColumnViewSet(ModelViewSet):
    queryset = Column.objects.all()
    serializer_class = serializers.ColumnSerializer


class LeaderboardViewSet(ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = serializers.LeaderboardSerializer

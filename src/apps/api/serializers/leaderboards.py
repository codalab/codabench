from requests import Response
from rest_framework import serializers, status
from leaderboards.models import Metric, Column, Leaderboard


class MetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = ('name', 'description', 'key', 'pk', 'id', )

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ('name', 'metric', 'leaderboard', 'id', 'pk', )


class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = ('name', 'competition',)
# api/serializers/submission_leaderboard.py
from rest_framework import serializers
from competitions.models import Submission
from leaderboards.models import SubmissionScore
from api.serializers.profiles import SimpleOrganizationSerializer


class SubmissionScoreSerializer(serializers.ModelSerializer):
    index = serializers.IntegerField(source='column.index', read_only=True)
    column_key = serializers.CharField(source='column.key', read_only=True)
    precision = serializers.IntegerField(source='column.precision', read_only=True)
    is_primary = serializers.SerializerMethodField()

    class Meta:
        model = SubmissionScore
        fields = ('id', 'index', 'score', 'column_key', 'precision', 'is_primary')

    def get_is_primary(self, obj):
        return obj.column.index == obj.column.leaderboard.primary_index


class SubmissionLeaderBoardSerializer(serializers.ModelSerializer):
    scores = SubmissionScoreSerializer(many=True)
    owner = serializers.CharField(source='owner.username')
    display_name = serializers.CharField(source='owner.display_name')
    slug_url = serializers.CharField(source='owner.slug_url')
    organization = SimpleOrganizationSerializer(allow_null=True)
    created_when = serializers.DateTimeField()
    queue_name = serializers.SerializerMethodField()
    queue_id = serializers.SerializerMethodField()
    queue_name = serializers.SerializerMethodField()

    def _get_effective_queue(self, obj):
        if obj.queue:
            return obj.queue

        if obj.parent and obj.parent.queue:
            return obj.parent.queue

        if (
            obj.phase
            and obj.phase.competition
            and obj.phase.competition.queue
        ):
            return obj.phase.competition.queue

        return None

    def get_queue_name(self, obj):
        queue = self._get_effective_queue(obj)
        return queue.name if queue else None

    def get_queue_id(self, obj):
        queue = self._get_effective_queue(obj)
        return queue.id if queue else None

    class Meta:
        model = Submission
        fields = (
            'id', 'parent', 'owner', 'leaderboard_id', 'fact_sheet_answers',
            'task', 'scores', 'display_name', 'slug_url', 'organization',
            'detailed_result', 'created_when', 'queue_name', 'queue_id', 'queue_name',
        )

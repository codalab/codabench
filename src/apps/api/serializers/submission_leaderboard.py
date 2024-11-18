# api/serializers/submission_leaderboard.py
from rest_framework import serializers
from competitions.models import Submission
from leaderboards.models import SubmissionScore
from api.serializers.profiles import SimpleOrganizationSerializer


class SubmissionScoreSerializer(serializers.ModelSerializer):
    index = serializers.IntegerField(source='column.index', read_only=True)
    column_key = serializers.CharField(source='column.key', read_only=True)

    class Meta:
        model = SubmissionScore
        fields = ('id', 'index', 'score', 'column_key')


class SubmissionLeaderBoardSerializer(serializers.ModelSerializer):
    scores = SubmissionScoreSerializer(many=True)
    owner = serializers.CharField(source='owner.username')
    display_name = serializers.CharField(source='owner.display_name')
    slug_url = serializers.CharField(source='owner.slug_url')
    organization = SimpleOrganizationSerializer(allow_null=True)
    created_when = serializers.DateTimeField()

    class Meta:
        model = Submission
        fields = (
            'id', 'parent', 'owner', 'leaderboard_id', 'fact_sheet_answers',
            'task', 'scores', 'display_name', 'slug_url', 'organization',
            'detailed_result', 'created_when'
        )

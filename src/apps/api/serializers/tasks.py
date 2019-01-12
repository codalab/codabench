from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from api.fields import NamedBase64ImageField, SlugWriteDictReadField
from api.serializers.datasets import DataSerializer
from api.serializers.leaderboards import LeaderboardSerializer
from competitions.models import Competition, Phase, Page, CompetitionCreationTaskStatus
from datasets.models import Data
from profiles.models import User
from tasks.models import Task, Solution


class TaskSerializer(WritableNestedModelSerializer):
    input_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    reference_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    scoring_program = SlugWriteDictReadField(read_serializer=DataSerializer, queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    ingestion_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    solutions = serializers.SlugRelatedField(queryset=Solution.objects.all(), required=False, allow_null=True, slug_field='key', many=True)

    class Meta:
        model = Task
        fields = [
            'name',
            'description',
            'key',
            'created_by',
            'created_when',
            'is_public',

            # Data pieces
            'input_data',
            'reference_data',
            'scoring_program',
            'ingestion_program',
            'solutions',
        ]

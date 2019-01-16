from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from api.fields import NamedBase64ImageField, SlugWriteDictReadField
from api.serializers.datasets import DataSerializer
from api.serializers.leaderboards import LeaderboardSerializer
from api.serializers.tasks import TaskSerializer
from competitions.models import Competition, Phase, Page, CompetitionCreationTaskStatus
from datasets.models import Data
from profiles.models import User
from tasks.models import Task


class PhaseSerializer(WritableNestedModelSerializer):
    input_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    reference_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    scoring_program = SlugWriteDictReadField(read_serializer=DataSerializer, queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    ingestion_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    public_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    starting_kit = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    tasks = serializers.SlugRelatedField(queryset=Task.objects.all(), required=False, allow_null=True, slug_field='key', many=True)

    class Meta:
        model = Phase
        fields = (
            'id',
            'index',
            'start',
            'end',
            'name',
            'description',
            'input_data',
            'reference_data',
            'scoring_program',
            'ingestion_program',
            'public_data',
            'starting_kit',

            'tasks',
            'is_task_and_solution',
        )

    def get_tasks(self, object):
        if type(object) is dict:
            return TaskSerializer(object)
        else:
            return serializers.SlugRelatedField(queryset=Task.objects.all(), required=False, allow_null=True, slug_field='key', many=True)


class PageSerializer(WritableNestedModelSerializer):
    # *NOTE* The competition property has to be replicated at the end of the file
    # after the CompetitionSerializer class is declared
    # competition = CompetitionSerializer(many=True)

    class Meta:
        model = Page
        fields = (
            'id',
            'title',
            'content',
            'index',
        )


class CompetitionSerializer(WritableNestedModelSerializer):
    created_by = serializers.SerializerMethodField(read_only=True)
    logo = NamedBase64ImageField(required=True)
    pages = PageSerializer(many=True)
    phases = PhaseSerializer(many=True)
    leaderboards = LeaderboardSerializer(many=True)
    collaborators = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Competition
        fields = (
            'id',
            'title',
            'created_by',
            'logo',
            'pages',
            'phases',
            'leaderboards',
            'collaborators',
        )

    def get_created_by(self, object):
        return str(object.created_by)

    def validate_leaderboards(self, value):
        if not value:
            raise serializers.ValidationError("Competitions require at least 1 leaderboard")
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context['created_by']
        return super().create(validated_data)


PageSerializer.competition = CompetitionSerializer(many=True, source='competition')


class CompetitionCreationTaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionCreationTaskStatus
        fields = (
            'status',
            'details',
            'resulting_competition',
        )

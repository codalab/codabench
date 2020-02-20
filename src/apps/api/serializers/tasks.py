from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from api.mixins import DefaultUserCreateMixin
from api.serializers.datasets import DataDetailSerializer, DataSimpleSerializer
from datasets.models import Data
from tasks.models import Task, Solution
from utils.data import make_url_sassy


class SolutionSerializer(WritableNestedModelSerializer):
    tasks = serializers.SlugRelatedField(queryset=Task.objects.all(), required=False, allow_null=True, slug_field='key', many=True)
    data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')

    class Meta:
        model = Solution
        fields = [
            'name',
            'description',
            'key',
            'tasks',
            'data',
            'md5',
        ]


class SolutionListSerializer(serializers.ModelSerializer):
    data = DataDetailSerializer()

    class Meta:
        model = Solution
        fields = (
            'name',
            'data'
        )


class TaskSerializer(DefaultUserCreateMixin, WritableNestedModelSerializer):
    input_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    ingestion_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    reference_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    scoring_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    validated = serializers.SerializerMethodField()

    class Meta:
        model = Task
        user_field = 'created_by'
        fields = (
            'id',
            'name',
            'description',
            'key',
            'created_by',
            'created_when',
            'is_public',
            'ingestion_only_during_scoring',
            'validated',

            # Data pieces
            'input_data',
            'ingestion_program',
            'reference_data',
            'scoring_program',
        )
        read_only_fields = (
            'created_by',
        )

    def get_validated(self, instance):
        return hasattr(instance, 'validated') and instance.validated is not None


class TaskDetailSerializer(WritableNestedModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True, required=False)
    input_data = DataSimpleSerializer(read_only=True)
    ingestion_program = DataSimpleSerializer(read_only=True)
    reference_data = DataSimpleSerializer(read_only=True)
    scoring_program = DataSimpleSerializer(read_only=True)
    solutions = SolutionSerializer(many=True, required=False, read_only=True)
    validated = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'description',
            'key',
            'created_by',
            'created_when',
            'is_public',
            'validated',

            # Data pieces
            'input_data',
            'ingestion_program',
            'reference_data',
            'scoring_program',
            'solutions',
        )

    def get_validated(self, task):
        return task.validated is not None


class TaskListSerializer(serializers.ModelSerializer):
    solutions = SolutionListSerializer(many=True, required=False, read_only=True)
    value = serializers.CharField(source='key', required=False)

    class Meta:
        model = Task
        fields = (
            'id',
            'created_when',
            'key',
            'name',
            'solutions',
            'ingestion_only_during_scoring',
            # Value is used for Semantic Multiselect dropdown api calls
            'value',
        )

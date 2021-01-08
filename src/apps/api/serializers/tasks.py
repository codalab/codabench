from profiles.models import User
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.mixins import DefaultUserCreateMixin
from api.serializers.datasets import DataDetailSerializer, DataSimpleSerializer
from competitions.models import PhaseTaskInstance, Phase
from datasets.models import Data
from tasks.models import Task, Solution


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
            'shared_with',
        )
        read_only_fields = (
            'created_by',
        )

    def validate_is_public(self, is_public):
        validated = Task.objects.get(id=self.instance.id)._validated
        if is_public and not validated:
            raise ValidationError('Task must be validated before it can be published')
        return is_public

    def get_validated(self, instance):
        return hasattr(instance, 'validated') and instance.validated is not None


class TaskDetailSerializer(WritableNestedModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True, required=False)
    input_data = DataSimpleSerializer(read_only=True)
    ingestion_program = DataSimpleSerializer(read_only=True)
    reference_data = DataSimpleSerializer(read_only=True)
    scoring_program = DataSimpleSerializer(read_only=True)
    solutions = SolutionSerializer(many=True, required=False, read_only=True)
    validated = serializers.SerializerMethodField(required=False)

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
    competitions = serializers.SerializerMethodField()
    shared_with = serializers.SerializerMethodField()

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
            'competitions',
            'shared_with',
        )

    def get_competitions(self, instance):
        return self.context['task_titles'][instance.pk]

    def get_shared_with(self, instance):
        return self.context['shared_with'][instance.pk]


class PhaseTaskInstanceSerializer(serializers.HyperlinkedModelSerializer):
    task = serializers.SlugRelatedField(queryset=Task.objects.all(), required=True, allow_null=False, slug_field='key',
                                        many=False)
    phase = serializers.PrimaryKeyRelatedField(many=False, queryset=Phase.objects.all())
    id = serializers.IntegerField(source='task.id', required=False)
    value = serializers.CharField(source='task.key', required=False)
    key = serializers.CharField(source='task.key', required=False)
    created_when = serializers.DateTimeField(source='task.created_when', required=False)
    name = serializers.CharField(source='task.name', required=False)

    class Meta:
        model = PhaseTaskInstance
        fields = (
            'task',
            'order_index',
            'phase',
            'id',
            # Value is used for Semantic Multiselect dropdown api calls
            'value',
            'key',
            'created_when',
            'name',
        )

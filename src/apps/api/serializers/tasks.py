from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from datasets.models import Data
from tasks.models import Task, Solution


class TaskSerializer(WritableNestedModelSerializer):
    input_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    ingestion_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    reference_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    scoring_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')

    class Meta:
        model = Task
        fields = [
            'id',
            'name',
            'description',
            'key',
            'created_by',
            'created_when',
            'is_public',

            # Data pieces
            'input_data',
            'ingestion_program',
            'reference_data',
            'scoring_program',
        ]

# TODO:// Simple serializer exists solely for Select2. Has a whole separate view and URL for using it. can this be done
#   with a get_serializer_call() method instead?


class TaskSerializerSimple(serializers.ModelSerializer):
    text = serializers.CharField(source='name')

    class Meta:
        model = Task
        fields = [
            'id',
            'key',
            'text',
        ]


class SolutionSerializer(WritableNestedModelSerializer):
    tasks = serializers.SlugRelatedField(queryset=Task.objects.all(), required=False, allow_null=True, slug_field='key', many=True)
    data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')

    class Meta:
        model = Solution
        fields = [
            'key',
            'tasks',
            'data',
        ]

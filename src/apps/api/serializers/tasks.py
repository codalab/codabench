from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from api.serializers.datasets import DataDetailSerializer
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


class TaskSerializer(WritableNestedModelSerializer):
    input_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    ingestion_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    reference_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    scoring_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    validated = serializers.SerializerMethodField()
    value = serializers.CharField(source='key', required=False)

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
            'ingestion_only_during_scoring',
            'validated',

            # The 'value' field helps semantic multiselect work with this stuff
            'value',

            # Data pieces
            'input_data',
            'ingestion_program',
            'reference_data',
            'scoring_program',
        )

    def get_validated(self, instance):
        return instance.validated is not None


class TaskDetailSerializer(WritableNestedModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True, required=False)
    input_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    ingestion_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    reference_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    scoring_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    solutions = SolutionSerializer(many=True, required=False, read_only=True)
    files = serializers.SerializerMethodField(read_only=True)
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
            'files',
            'solutions',
        )

    def get_files(self, task):
        files = []
        file_types = [
            ('input_data', task.input_data),
            ('ingestion_program', task.ingestion_program),
            ('reference_data', task.reference_data),
            ('scoring_program', task.scoring_program),
        ]
        for label, program in file_types:
            if program:
                files.append({
                    "name": label,
                    "file_path": make_url_sassy(program.data_file.name),
                })
        return files

    def get_validated(self, task):
        return task.validated is not None


class TaskListSerializer(serializers.ModelSerializer):
    solutions = SolutionListSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Task
        fields = (
            'key',
            'name',
            'solutions',
            'ingestion_only_during_scoring'
        )

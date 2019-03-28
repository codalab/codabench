from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from datasets.models import Data
from tasks.models import Task, Solution
from utils.data import make_url_sassy


class SolutionSerializer(WritableNestedModelSerializer):
    tasks = serializers.SlugRelatedField(queryset=Task.objects.all(), required=False, allow_null=True, slug_field='key', many=True)
    data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    file_path = serializers.SerializerMethodField(read_only=True, required=False)

    class Meta:
        model = Solution
        fields = [
            'key',
            'tasks',
            'data',
            'file_path',
        ]

    def get_file_path(self, solution):
        return make_url_sassy(solution.data.data_file.name)


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


class TaskDetailSerializer(WritableNestedModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True, required=False)
    input_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    ingestion_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    reference_data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    scoring_program = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    solutions = SolutionSerializer(many=True, required=False, read_only=True)
    files = serializers.SerializerMethodField(read_only=True)

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
            'files',
            'solutions',
        ]

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

# TODO:// Simple serializer exists solely for Select2. Has a whole separate view and URL for using it. can this be done
#   with a get_serializer_call() method instead?


class TaskSerializerSimple(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = [
            'id',
            'key',
            'name',
        ]

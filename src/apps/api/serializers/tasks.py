from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from api.mixins import DefaultUserCreateMixin
from api.serializers.datasets import DataDetailSerializer, DataSimpleSerializer
from competitions.models import PhaseTaskInstance, Phase
from datasets.access import user_can_access_task_dataset, user_can_access_task_solution
from datasets.models import Data
from tasks.models import Task, Solution
from competitions.models import Competition


class SolutionSerializer(WritableNestedModelSerializer):
    tasks = serializers.SlugRelatedField(queryset=Task.objects.all(), required=False, allow_null=True, slug_field='key', many=True)
    data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    size = serializers.SerializerMethodField()

    class Meta:
        model = Solution
        fields = [
            'name',
            'description',
            'key',
            'tasks',
            'data',
            'md5',
            'size',
        ]

    def get_size(self, instance):
        try:
            return instance.data.file_size
        except AttributeError:
            print("This solution has no data associated with it...might be a test")
            return None


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

    def get_validated(self, instance):
        # We should get the results of TaskViewSet's evaluation
        # for whether a task is validated or not vs just whether
        # or not the attribute 'validated' exists...it could be false.
        return getattr(instance, 'validated', False)


class TaskDetailSerializer(WritableNestedModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    owner_display_name = serializers.SerializerMethodField()
    input_data = DataSimpleSerializer(read_only=True)
    ingestion_program = DataSimpleSerializer(read_only=True)
    reference_data = DataSimpleSerializer(read_only=True)
    scoring_program = DataSimpleSerializer(read_only=True)
    solutions = SolutionSerializer(many=True, required=False, read_only=True)
    validated = serializers.SerializerMethodField(required=False)
    shared_with = serializers.SerializerMethodField()
    competitions = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'description',
            'created_by',
            'owner_display_name',
            'created_when',
            'is_public',
            'validated',
            'shared_with',
            'competitions',

            # Data pieces
            'input_data',
            'ingestion_program',
            'reference_data',
            'scoring_program',
            'solutions',
        )

    def get_validated(self, instance):
        # We should get the results of TaskViewSet's evaluation
        # for whether a task is validated or not vs just whether
        # or not the attribute 'validated' exists...it could be false.
        return getattr(instance, 'validated', False)

    def get_competitions(self, instance):

        # Fech competitions which hase phases with this task
        # competitions = Phase.objects.filter(tasks__in=[instance.pk]).values('competition')
        competitions = Competition.objects.filter(phases__tasks__in=[instance.pk]).values("id", "title").distinct()

        return competitions

    def get_shared_with(self, instance):
        # Fetch the users with whom the task is shared
        shared_users = instance.shared_with.all()
        return [user.username for user in shared_users]

    def get_owner_display_name(self, instance):
        # Get the user's display name if not None, otherwise return username
        return instance.created_by.display_name if instance.created_by.display_name else instance.created_by.username


class TaskListSerializer(serializers.ModelSerializer):
    solutions = SolutionListSerializer(many=True, required=False, read_only=True)
    value = serializers.CharField(source='key', required=False)
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    owner_display_name = serializers.SerializerMethodField()
    is_used_in_competitions = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            'id',
            'created_when',
            'created_by',
            'owner_display_name',
            'key',
            'name',
            'description',
            'solutions',
            'ingestion_only_during_scoring',
            # Value is used for Semantic Multiselect dropdown api calls
            'value',
            'is_public',
            'is_used_in_competitions',
        )

    def get_is_used_in_competitions(self, instance):

        # Count competitions that are using this task
        num_competitions = Competition.objects.filter(phases__tasks__in=[instance.pk]).distinct().count()

        return num_competitions > 0

    def get_shared_with(self, instance):
        return self.context['shared_with'][instance.pk]

    def get_owner_display_name(self, instance):
        # Get the user's display name if not None, otherwise return username
        return instance.created_by.display_name if instance.created_by.display_name else instance.created_by.username


class PhaseTaskInstanceSerializer(serializers.HyperlinkedModelSerializer):
    task = serializers.SlugRelatedField(queryset=Task.objects.all(), required=True, allow_null=False, slug_field='key',
                                        many=False)
    phase = serializers.PrimaryKeyRelatedField(many=False, queryset=Phase.objects.all())
    id = serializers.IntegerField(source='task.id', required=False)
    value = serializers.CharField(source='task.key', required=False)
    key = serializers.CharField(source='task.key', required=False)
    created_when = serializers.DateTimeField(source='task.created_when', required=False)
    name = serializers.CharField(source='task.name', required=False)
    solutions = serializers.SerializerMethodField()
    public_datasets = serializers.SerializerMethodField()

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
            'solutions',
            'public_datasets'
        )

    def get_solutions(self, instance):
        qs = instance.task.solutions.all()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        qs = [
            solution for solution in qs
            if user_can_access_task_solution(user, instance.phase, solution)
        ]
        return SolutionSerializer(qs, many=True).data

    def get_public_datasets(self, instance):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        datasets = [
            instance.task.input_data,
            instance.task.reference_data,
            instance.task.ingestion_program,
            instance.task.scoring_program,
        ]
        datasets = [
            dataset for dataset in datasets
            if user_can_access_task_dataset(user, instance.phase, dataset)
        ]

        try:
            return DataDetailSerializer(datasets, many=True).data
        except Exception:
            # No datasets or programs to return
            return []

from django.db.models import Sum, Q
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from api.serializers.submission_leaderboard import SubmissionLeaderBoardSerializer

from competitions.models import Submission, Phase
from leaderboards.models import Leaderboard, Column

from .fields import CharacterSeparatedField
from .tasks import PhaseTaskInstanceSerializer


class ColumnSerializer(WritableNestedModelSerializer):
    computation_indexes = CharacterSeparatedField(allow_null=True, required=False)

    class Meta:
        model = Column
        fields = (
            'id',
            'computation',
            'computation_indexes',
            'title',
            'key',
            'sorting',
            'index',
            'hidden',
            'precision',
        )

    def validate(self, attrs):
        if 'computation' in attrs and 'computation_indexes' not in attrs:
            raise serializers.ValidationError(
                "Column with computation must have at least 1 column selected for the computation to act upon")

        if 'computation_indexes' in attrs and attrs['computation_indexes']:
            if 'computation' not in attrs:
                raise serializers.ValidationError("Cannot add computation columns without a computation function set")

            if str(attrs["index"]) in attrs["computation_indexes"].split(","):
                raise serializers.ValidationError(
                    f"Column with index {attrs['index']} referencing itself. Cannot self-reference, must be other columns.")

        return attrs


class LeaderboardSerializer(WritableNestedModelSerializer):
    columns = ColumnSerializer(many=True)

    class Meta:
        model = Leaderboard
        fields = (
            'id',
            'primary_index',
            'title',
            'key',
            'columns',
            'hidden',
            'submission_rule',
        )

    def validate_columns(self, columns):
        if not columns:
            raise serializers.ValidationError("Leaderboards require at least 1 column")

        # Make sure all column indexes are unique
        indexes = [column['index'] for column in columns]
        if len(set(indexes)) != len(columns):
            raise serializers.ValidationError("Columns must have unique indexes!")

        # Make sure all column keys are unique
        keys = [column["key"] for column in columns]
        if len(set(keys)) != len(columns):
            raise serializers.ValidationError("Columns must have unique keys!")

        # Validate that column.computation_indexes points to valid columns
        for column in columns:
            if 'computation_indexes' in column and column['computation_indexes']:
                for index in column['computation_indexes'].split(","):
                    try:
                        if int(index) not in indexes:
                            raise serializers.ValidationError(
                                f"Column index {index} does not exist in available indexes {indexes}")
                    except ValueError:
                        raise serializers.ValidationError(
                            f"Bad value for index, should be an integer but received: {index}.")

        return columns


class LeaderboardEntriesSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Leaderboard
        fields = (
            'submissions',
        )

    def get_submissions(self, instance):
        # desc == -colname
        # asc == colname
        primary_col = instance.columns.get(index=instance.primary_index)
        # Order first by primary column. Then order by other columns after for tie breakers.
        ordering = [f'{"-" if primary_col.sorting == "desc" else ""}primary_col']
        submissions = Submission.objects.filter(leaderboard=instance, is_specific_task_re_run=False)\
            .select_related('owner').prefetch_related('scores')\
            .annotate(primary_col=Sum('scores__score', filter=Q(scores__column=primary_col)))
        # TODO: Look at why we have primary_col in the above annotation

        for column in instance.columns.exclude(id=primary_col.id).order_by('index'):
            col_name = f'col{column.index}'
            ordering.append(f'{"-" if column.sorting == "desc" else ""}{col_name}')
            kwargs = {
                col_name: Sum('scores__score', filter=Q(scores__column__index=column.index))
            }
            submissions = submissions.annotate(**kwargs)

        submissions = submissions.order_by(*ordering, 'created_when')
        return SubmissionLeaderBoardSerializer(submissions, many=True).data


class LeaderboardPhaseSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField(read_only=True)
    columns = serializers.SerializerMethodField()
    tasks = PhaseTaskInstanceSerializer(source='task_instances', many=True)
    primary_index = serializers.SerializerMethodField()

    def get_columns(self, instance):
        columns = Column.objects.filter(leaderboard=instance.leaderboard, hidden=False)
        if len(columns) == 0:
            raise serializers.ValidationError("No columns exist on the leaderboard")
        else:
            return ColumnSerializer(columns, many=len(columns) >= 1).data

    def get_primary_index(self, instance):
        return instance.leaderboard.primary_index

    class Meta:
        model = Phase
        fields = (
            'id',
            'name',
            'submissions',
            'tasks',
            'leaderboard',
            'columns',
            'primary_index',
        )
        depth = 1

    def get_submissions(self, instance):
        # desc == -colname
        # asc == colname
        primary_col = instance.leaderboard.columns.get(index=instance.leaderboard.primary_index)
        ordering = [f'{"-" if primary_col.sorting == "desc" else ""}primary_col']
        submissions = Submission.objects.filter(
            phase=instance,
            is_soft_deleted=False,
            has_children=False,
            is_specific_task_re_run=False,
            leaderboard__isnull=False, ) \
            .select_related('owner').prefetch_related('scores') \
            .annotate(primary_col=Sum('scores__score', filter=Q(scores__column=primary_col)))

        for column in instance.leaderboard.columns.exclude(id=primary_col.id, hidden=False).order_by('index'):
            col_name = f'col{column.index}'
            ordering.append(f'{"-" if column.sorting == "desc" else ""}{col_name}')
            kwargs = {
                col_name: Sum('scores__score', filter=Q(scores__column__index=column.index))
            }
            submissions = submissions.annotate(**kwargs)

        submissions = submissions.order_by(*ordering, 'created_when')
        return SubmissionLeaderBoardSerializer(submissions, many=True).data

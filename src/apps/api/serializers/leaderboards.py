from django.db.models import Sum, Q
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from api.serializers.submissions import SubmissionLeaderBoardSerializer
from leaderboards.models import Leaderboard, Column

from .fields import CharacterSeparatedField


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
        )

    def validate(self, attrs):
        if 'computation' in attrs and 'computation_indexes' not in attrs:
            raise serializers.ValidationError("Column with computation must have at least 1 column selected for the computation to act upon")

        if 'computation_indexes' in attrs and attrs['computation_indexes']:
            if 'computation' not in attrs:
                raise serializers.ValidationError("Cannot add computation columns without a computation function set")

            if str(attrs["index"]) in attrs["computation_indexes"].split(","):
                raise serializers.ValidationError(f"Column with index {attrs['index']} referencing itself. Cannot self-reference, must be other columns.")

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
                            raise serializers.ValidationError(f"Column index {index} does not exist in available indexes {indexes}")
                    except ValueError:
                        raise serializers.ValidationError(f"Bad value for index, should be an integer but received: {index}.")

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
        print("\n\n\n\nhere\n\n\n\n")
        primary_col = instance.columns.get(index=instance.primary_index)
        ordering = [f'{"-" if primary_col.sorting == "desc" else ""}primary_col']
        submissions = instance.submissions.all().select_related('owner').prefetch_related('scores').annotate(primary_col=Sum('scores__score', filter=Q(scores__column=primary_col)))

        for column in instance.columns.exclude(id=primary_col.id).order_by('index'):
            col_name = f'col{column.index}'
            ordering.append(f'{"-" if column.sorting == "desc" else ""}{col_name}')
            kwargs = {
                col_name: Sum('scores__score', filter=Q(scores__column__index=column.index))
            }
            submissions = submissions.annotate(**kwargs)

        submissions = submissions.order_by(*ordering, 'created_when')
        return SubmissionLeaderBoardSerializer(submissions, many=True).data

from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
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


# class ScoresSerializer(serializers.Serializer):
#

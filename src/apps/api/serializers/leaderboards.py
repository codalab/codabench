from drf_writable_nested import WritableNestedModelSerializer
from leaderboards.models import Leaderboard, Column


class ColumnSerializer(WritableNestedModelSerializer):
    class Meta:
        model = Column
        fields = (
            'leaderboard',
            'computation',
            'computation_columns',
            'title',
            'key',
            'sorting',
            'index',
        )


class LeaderboardSerializer(WritableNestedModelSerializer):
    columns = ColumnSerializer(many=True)

    class Meta:
        model = Leaderboard
        fields = (
            'competition',
            'primary_column',
            'title',
            'key',
            'columns',
        )

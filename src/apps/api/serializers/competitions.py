from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from api.serializers.leaderboards import LeaderboardSerializer
from competitions.models import Competition, Phase, Submission, Page
from profiles.models import User


class PhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = (
            'competition',
            'number',
            'start',
            'end',
            'description',
            'input_data',
            'reference_data',
            'scoring_program',
            'ingestion_program',
            'public_data',
            'starting_kit',
        )


class PageSerializer(serializers.ModelSerializer):
    # *NOTE* The competition property has to be replicated at the end of the file
    # after the CompetitionSerializer class is declared
    # competition = CompetitionSerializer(many=True)

    class Meta:
        model = Page
        fields = (
            'competition',
            'title',
            'content',
            'index',
        )


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ('phase',)


class CompetitionSerializer(WritableNestedModelSerializer):
    created_by = serializers.SerializerMethodField(read_only=True)
    pages = PageSerializer(many=True)
    # phases = PhaseSerializer(many=True)
    # leaderboards = LeaderboardSerializer(many=True)
    # collaborators = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Competition
        fields = (
            'id',
            'title',
            'created_by',
            'pages',
            # 'phases',
            # 'leaderboards',
            # 'collaborators',
        )

    def get_created_by(self, object):
        return str(object.created_by)

    # def create(self, validated_data):
    #     validated_data["created_by"] = self.context['created_by']
    #     print(validated_data)
    #     return super().create(validated_data)


PageSerializer.competition = CompetitionSerializer(many=True, source='competition')

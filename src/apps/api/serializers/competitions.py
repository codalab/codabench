from rest_framework import serializers
from competitions.models import Competition, Phase, Submission


class CompetitionSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Competition
        fields = ('title', 'created_by')

    def get_created_by(self, object):
        return str(object.created_by)


class PhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = ('competition',)


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ('phase',)

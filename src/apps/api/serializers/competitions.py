from rest_framework import serializers
from competitions.models import Competition, Phase, Submission


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ('title',)


class PhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = ('competition',)


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ('phase',)

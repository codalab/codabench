from rest_framework import serializers
from competitions.models import Competition, Phase, Submission


class CompetitionSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Competition
        fields = ('id', 'title', 'created_by')

    def get_created_by(self, object):
        return str(object.created_by)

    def create(self, validated_data):
        validated_data["created_by"] = self.context['created_by']
        return super().create(validated_data)


class PhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = ('competition',)


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ('phase',)

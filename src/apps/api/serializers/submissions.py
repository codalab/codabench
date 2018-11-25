from rest_framework import serializers

from competitions.models import Submission
from datasets.models import Data


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = (
            'phase',
            'name',
            'description',
            'pk',
            'id',
            'created_when',
            'is_public',
            'status',
            'status_details',
            'secret',
        )
        extra_kwargs = {
            "secret": {
                "write_only": True
            }
        }

    def update(self, instance, validated_data):
        if instance.secret != validated_data.get('secret'):
            raise PermissionError("Submission secret invalid")

        print("Updated to...")
        print(validated_data)

        if validated_data["status"] == Submission.SCORING:
            # Start scoring because we're "SCORING" status now from compute worker
            from competitions.tasks import run_submission
            run_submission(instance.pk, is_scoring=True)
        return super().update(instance, validated_data)


class SubmissionCreationSerializer(serializers.ModelSerializer):
    data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')

    class Meta:
        model = Submission
        fields = (
            'data',
            'phase',
        )

    # TODO: Validate the user is a participant in this competition.phase

    def create(self, validated_data):
        validated_data["owner"] = self.context['owner']
        sub = super().create(validated_data)
        sub.start()
        return sub


# class SubmissionScores(serializers.Serializer):


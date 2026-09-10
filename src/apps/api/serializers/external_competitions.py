from rest_framework import serializers

from external_competitions.models import ExternalCompetition, ExternalPlatform


class ExternalCompetitionSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    platform_type = serializers.CharField(source='platform.platform_type', read_only=True)

    class Meta:
        model = ExternalCompetition
        fields = (
            'id',
            'name',
            'description',
            'image_url',
            'organizer_name',
            'competition_url',
            'competition_created_when',
            'competition_started_when',
            'platform',
            'platform_name',
            'platform_type',
        )


class ExternalPlatformFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalPlatform
        fields = ('id', 'name', 'platform_type')

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.mixins import DefaultUserCreateMixin
from datasets.models import Data, DataGroup
from competitions.models import CompetitionCreationTaskStatus, CompetitionDump


class DataSerializer(DefaultUserCreateMixin, serializers.ModelSerializer):
    request_sassy_file_name = serializers.CharField(required=True, max_length=255, write_only=True)

    class Meta:
        model = Data
        user_field = 'created_by'
        fields = (
            'created_when',
            'name',
            'type',
            'description',
            'is_public',
            'request_sassy_file_name',
            'in_use',
            'id',
            'key',
            'created_by',
            'data_file',
            'was_created_by_competition',
            'competition',
            'file_name',

        )
        read_only_fields = (
            'key',
            'created_by',
            'data_file',
            'was_created_by_competition',
        )

    def validate_is_public(self, is_public):
        if self.instance:
            if self.instance.submission.exists():
                md5 = self.instance.submission.first().md5
                if is_public and md5 is None:
                    raise ValidationError('Submission must be validated before it can be published')
        return is_public

    def validate(self, attrs):
        if 'name' in attrs:
            existing_lookup = Data.objects.filter(name=attrs['name'], created_by=self.context['request'].user)
            if self.instance:
                existing_lookup = existing_lookup.exclude(pk=self.instance.pk)
            if existing_lookup.exists():
                raise ValidationError("You already have a dataset by this name, please delete that dataset or rename this one")
        return attrs

    def create(self, validated_data):
        # Pop this non-model field before we create the model using all validated_data
        request_sassy_file_name = validated_data.pop('request_sassy_file_name', None)

        instance = super().create(validated_data)
        instance.request_sassy_file_name = request_sassy_file_name
        return instance


class DataSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Data
        fields = (
            'id',
            'type',
            'name',
            'key',
        )


class DataDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    owner_display_name = serializers.SerializerMethodField()
    competition = serializers.SerializerMethodField()
    value = serializers.CharField(source='key', required=False)

    class Meta:
        model = Data
        fields = (
            'id',
            'created_by',
            'owner_display_name',
            'created_when',
            'name',
            'type',
            'description',
            'is_public',
            'key',
            # Value is used for Semantic Multiselect dropdown api calls
            'value',
            'was_created_by_competition',
            'in_use',
            'file_size',
            'competition',
            'file_name',
        )

    def get_competition(self, obj):
        if obj.competition:
            # Submission
            return {
                "id": obj.competition.id,
                "title": obj.competition.title,
            }
        else:
            competition = None
            try:
                # Check if it is a bundle
                competition = CompetitionCreationTaskStatus.objects.get(dataset=obj).resulting_competition
            except CompetitionCreationTaskStatus.DoesNotExist:
                competition = None
            if not competition:
                # Check if it is a dump
                try:
                    competition = CompetitionDump.objects.get(dataset=obj).competition
                except CompetitionDump.DoesNotExist:
                    competition = None

            if competition:
                return {
                    "id": competition.id,
                    "title": competition.title
                }

        return None

    def get_owner_display_name(self, instance):
        return instance.created_by.display_name if instance.created_by.display_name else instance.created_by.username


class DataGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataGroup
        fields = (
            'created_by',
            'created_when',
            'name',
            'datas',
        )

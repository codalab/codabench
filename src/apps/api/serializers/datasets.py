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
    file_size = serializers.SerializerMethodField()
    value = serializers.CharField(source='key', required=False)

    # These fields will be conditionally returned for type == SUBMISSION only
    submission_file_size = serializers.SerializerMethodField()
    prediction_result_file_size = serializers.SerializerMethodField()
    scoring_result_file_size = serializers.SerializerMethodField()
    detailed_result_file_size = serializers.SerializerMethodField()

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
            'competition',
            'file_name',
            'file_size',
            'submission_file_size',
            'prediction_result_file_size',
            'scoring_result_file_size',
            'detailed_result_file_size',
        )

    def to_representation(self, instance):
        """
        Called automatically by DRF when serializing a model instance to JSON.

        This method customizes the serialized output of the DataDetailSerializer.
        Specifically, it removes detailed file size fields when the data type is not 'SUBMISSION'.

        Example: For input_data or scoring_program types, submission-related fields
        are not relevant and will be excluded from the output.
        """
        # First, generate the default serialized representation using the parent method
        rep = super().to_representation(instance)

        # If this data object is NOT of type 'submission', remove the following fields
        if instance.type != Data.SUBMISSION:
            # These fields are only meaningful for submission-type data
            rep.pop('submission_file_size', None)
            rep.pop('prediction_result_file_size', None)
            rep.pop('scoring_result_file_size', None)
            rep.pop('detailed_result_file_size', None)

        # Return the final customized representation
        return rep

    def get_file_size(self, obj):
        # Check if the data object is of type 'SUBMISSION'
        if obj.type == Data.SUBMISSION:
            # Start with the base file size of the data file itself (if present)
            total_size = obj.file_size or 0

            # Loop through all submissions that use this data
            for submission in obj.submission.all():
                # Add the size of the prediction result file (if any)
                total_size += submission.prediction_result_file_size or 0
                # Add the size of the scoring result file (if any)
                total_size += submission.scoring_result_file_size or 0
                # Add the size of the detailed result file (if any)
                total_size += submission.detailed_result_file_size or 0

            # Return the combined size of data file and all associated result files
            return total_size

        # For non-submission data types, just return the file size as-is
        return obj.file_size

    def get_submission_file_size(self, obj):
        return obj.file_size or 0

    def get_prediction_result_file_size(self, obj):
        return sum([s.prediction_result_file_size or 0 for s in obj.submission.all()])

    def get_scoring_result_file_size(self, obj):
        return sum([s.scoring_result_file_size or 0 for s in obj.submission.all()])

    def get_detailed_result_file_size(self, obj):
        return sum([s.detailed_result_file_size or 0 for s in obj.submission.all()])

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

from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import FileField

from datasets.models import Data, DataGroup


class DataSerializer(serializers.ModelSerializer):
    # data_file = FileField(allow_empty_file=False)

    class Meta:
        model = Data
        fields = (
            'created_by',
            'created_when',
            'name',
            'type',
            'description',
            'data_file',
            'key',
        )
        read_only_fields = (
            'owner',
            'key',
            'created_by',
            'created_when',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Should only be changing data_file if we're using local storage!!!

        # Fix the URL, should be the full URL with correct path
        upload_path = '{}{}'.format(settings.MEDIA_URL, instance.data_file)
        representation["data_file"] = self.context['request'].build_absolute_uri(upload_path)

        return representation

    def create(self, validated_data):
        validated_data["created_by"] = self.context['request'].user
        return super().create(validated_data)



class DataGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataGroup
        fields = (
            'created_by',
            'created_when',
            'name',
            'datas',
        )

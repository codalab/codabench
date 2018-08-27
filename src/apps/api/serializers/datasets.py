import os

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from datasets.models import Data, DataGroup


class DataSerializer(serializers.ModelSerializer):
    request_sassy_file_name = serializers.CharField(required=True, max_length=255, write_only=True)

    class Meta:
        model = Data
        fields = (
            'id',
            'created_by',
            'created_when',
            'name',
            'type',
            'description',
            'data_file',
            'is_public',
            'key',
            'request_sassy_file_name',
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "key": {"read_only": True},
            "created_by": {"read_only": True},
        }

    def validate_name(self, name):
        if name and Data.objects.filter(name=name, created_by=self.context['created_by']).exists():
            raise ValidationError("You already have a dataset by this name, please delete that dataset or rename this one")
        return name

    def create(self, validated_data):
        # Pop this non-model field before we create the model using all validated_data
        request_sassy_file_name = validated_data.pop('request_sassy_file_name', None)

        validated_data["created_by"] = self.context['created_by']
        instance = super().create(validated_data)
        instance.request_sassy_file_name = request_sassy_file_name
        return instance


class DataGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataGroup
        fields = (
            'created_by',
            'created_when',
            'name',
            'datas',
        )

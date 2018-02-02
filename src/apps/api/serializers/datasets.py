from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from datasets.models import Data, DataGroup


class DataSerializer(serializers.ModelSerializer):
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
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "key": {"read_only": True},
            "created_by": {"read_only": True},
        }

    def validate_name(self, name):
        if Data.objects.filter(name=name, created_by=self.context['created_by']).exists():
            raise ValidationError("You already have a dataset by this name, please delete that dataset or rename this one")
        return name

    def create(self, validated_data):
        validated_data["created_by"] = self.context['created_by']
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

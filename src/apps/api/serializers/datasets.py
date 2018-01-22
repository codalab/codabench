from rest_framework import serializers
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
            'key',
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "key": {"read_only": True}
        }


class DataGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataGroup
        fields = (
            'created_by',
            'created_when',
            'name',
            'datas',
        )

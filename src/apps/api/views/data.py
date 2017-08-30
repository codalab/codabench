from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView

from api import serializers
from datasets.models import Data, DataGroup


class DataViewSet(ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView, GenericViewSet):
    queryset = Data.objects.all()
    serializer_class = serializers.DataSerializer


class DataGroupViewSet(ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView, GenericViewSet):
    queryset = DataGroup.objects.all()
    serializer_class = serializers.DataGroupSerializer

from rest_framework import mixins
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers import datasets as serializers
from datasets.models import Data, DataGroup


class DataViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  # mixins.UpdateModelMixin,  # We don't update datasets!
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Data.objects.all()
    serializer_class = serializers.DataSerializer

    def get_serializer_context(self):
        return {
            "created_by": self.request.user
        }


class DataGroupViewSet(ModelViewSet):
    queryset = DataGroup.objects.all()
    serializer_class = serializers.DataGroupSerializer

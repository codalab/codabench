from uuid import UUID

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import SearchFilter
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
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('type', 'name')
    search_fields = ('name', 'description',)

    def get_queryset(self):
        query = self.request.query_params.get('q', None)

        filters = Q(is_public=True) | Q(created_by=self.request.user)

        # Check if they are searching for a UUID
        if query is not None and len(query) > 15:
            try:
                filters |= Q(key=UUID(query))
            except ValueError:
                # Not a valid uuid, ignore
                pass

        return Data.objects.filter(filters)

    def get_serializer_context(self):
        return {
            "created_by": self.request.user
        }


class DataGroupViewSet(ModelViewSet):
    queryset = DataGroup.objects.all()
    serializer_class = serializers.DataGroupSerializer
